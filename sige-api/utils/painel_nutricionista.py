from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Case, Count, DecimalField, F, Q, Sum, Value, When
from django.utils import timezone

from cadastro.models import ItemGenerico
from empenho.models import Empenho, ItemEmpenho, OperacaoItem
from entrega.models import ItemOrdem
from estoque.models import LoteEstoque, MovimentacaoEstoque
from licitacao.models import Ata, ItemAta
from utils.estoque_services import FUSO_ESTOQUE, data_atual_estoque


ZERO = Decimal('0')
SEMANAS_MOVIMENTACAO = 8


def _disponibilidade_por_genero(hoje):
    """
    Para cada gênero, o que o Nutricionista pode contar para montar o cardápio,
    do mais imediato ao mais distante: em estoque, a caminho (ordens emitidas e
    ainda não entregues), empenhado sem ordem e o saldo livre nas ARPs.
    """
    em_estoque = dict(
        LoteEstoque.objects.filter(saldo_atual__gt=0)
        .filter(
            Q(legado=True)
            | Q(legado=False, data_validade__gte=hoje)
        )
        .values('estoque__item_generico_id')
        .annotate(total=Sum('saldo_atual'))
        .values_list('estoque__item_generico_id', 'total')
    )

    a_caminho = dict(
        ItemOrdem.objects.exclude(ordem_entrega__status='con')
        .values('item_empenho__item_ata__item_generico_id')
        .annotate(total=Sum(F('quantidade_solicitada') - F('quantidade_entregue')))
        .values_list('item_empenho__item_ata__item_generico_id', 'total')
    )

    empenhado = dict(
        ItemEmpenho.objects.values('item_ata__item_generico_id')
        .annotate(total=Sum('quantidade_atual'))
        .values_list('item_ata__item_generico_id', 'total')
    )

    # Mesma regra de empenho.services.saldo_disponivel_ata, agregada por item da ARP.
    comprometido_por_item_ata = dict(
        OperacaoItem.objects.values('item_empenho__item_ata_id')
        .annotate(total=Sum(Case(
            When(tipo__in=['inc', 'ref'], then=F('valor')),
            When(tipo='anl', then=-F('valor')),
            default=Value(Decimal('0.00')),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )))
        .values_list('item_empenho__item_ata_id', 'total')
    )
    na_arp = defaultdict(lambda: ZERO)
    for item_ata in ItemAta.objects.values('id', 'item_generico_id', 'quantidade_licitada'):
        livre = item_ata['quantidade_licitada'] - (comprometido_por_item_ata.get(item_ata['id']) or ZERO)
        na_arp[item_ata['item_generico_id']] += max(livre, ZERO)

    generos = []
    for genero in ItemGenerico.objects.order_by('categoria', 'descricao'):
        generos.append({
            'item_generico_id': genero.id,
            'catmat': genero.catmat,
            'descricao': genero.descricao,
            'unidade_medida': genero.unidade_medida,
            'categoria': genero.categoria,
            'categoria_descricao': genero.get_categoria_display(),
            'em_estoque': em_estoque.get(genero.id) or ZERO,
            'a_caminho': max(a_caminho.get(genero.id) or ZERO, ZERO),
            'empenhado': empenhado.get(genero.id) or ZERO,
            'na_arp': na_arp[genero.id],
        })
    return generos


def _resumo_validades(hoje):
    limite = hoje + timedelta(days=30)
    return LoteEstoque.objects.filter(
        saldo_atual__gt=0,
        legado=False,
        data_validade__gte=hoje,
        data_validade__lte=limite,
    ).aggregate(
        total_proximos=Count('id'),
        vence_hoje=Count('id', filter=Q(data_validade=hoje)),
        criticos=Count(
            'id',
            filter=Q(
                data_validade__gte=hoje + timedelta(days=1),
                data_validade__lte=hoje + timedelta(days=7),
            ),
        ),
        atencao=Count(
            'id',
            filter=Q(
                data_validade__gte=hoje + timedelta(days=8),
                data_validade__lte=limite,
            ),
        ),
    )


def _movimentacao_semanal(hoje):
    """Entradas e saídas de cada gênero nas últimas semanas (segunda a domingo)."""
    inicio_semana_atual = hoje - timedelta(days=hoje.weekday())
    semanas = [inicio_semana_atual - timedelta(weeks=n) for n in range(SEMANAS_MOVIMENTACAO - 1, -1, -1)]
    inicio = timezone.make_aware(datetime.combine(semanas[0], time.min), FUSO_ESTOQUE)

    por_genero = {}
    movimentos = MovimentacaoEstoque.objects.filter(data_hora__gte=inicio).values(
        'estoque__item_generico_id', 'sentido', 'quantidade', 'data_hora',
    )
    for movimento in movimentos:
        dia = timezone.localtime(movimento['data_hora'], FUSO_ESTOQUE).date()
        indice = (dia - semanas[0]).days // 7
        if not 0 <= indice < SEMANAS_MOVIMENTACAO:
            continue
        serie = por_genero.setdefault(movimento['estoque__item_generico_id'], {
            'entradas': [ZERO] * SEMANAS_MOVIMENTACAO,
            'saidas': [ZERO] * SEMANAS_MOVIMENTACAO,
        })
        chave = 'entradas' if movimento['sentido'] == MovimentacaoEstoque.Sentido.ENTRADA else 'saidas'
        serie[chave][indice] += movimento['quantidade']

    return {
        'semanas': [semana.isoformat() for semana in semanas],
        'por_genero': por_genero,
    }


def _saldos_empenhos():
    return [
        {
            'id': empenho.id,
            'codigo': empenho.codigo,
            'fornecedor': empenho.ata.fornecedor.nome_fantasia,
            'valor_total': empenho.valor_total,
            'valor_utilizado': empenho.saldo_utilizado,
            'saldo_disponivel': max(empenho.valor_total - empenho.saldo_utilizado, ZERO),
        }
        for empenho in Empenho.objects.select_related('ata__fornecedor').order_by('codigo')
    ]


def _saldos_arps():
    atas = Ata.objects.select_related('fornecedor', 'licitacao').annotate(
        valor_registrado=Sum(
            F('itemata__quantidade_licitada') * F('itemata__valor_unitario'),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
    ).order_by('numero_ata')
    return [
        {
            'id': ata.id,
            'numero_ata': ata.numero_ata,
            'fornecedor': ata.fornecedor.nome_fantasia,
            'licitacao': ata.licitacao.numero_licitacao,
            'valor_registrado': ata.valor_registrado or ZERO,
            'saldo_disponivel': ata.ata_saldo_total,
        }
        for ata in atas
    ]


def montar_painel(hoje=None):
    referencia = hoje or data_atual_estoque()
    return {
        'generos': _disponibilidade_por_genero(referencia),
        'movimentacao': _movimentacao_semanal(referencia),
        'empenhos': _saldos_empenhos(),
        'arps': _saldos_arps(),
        'validades': _resumo_validades(referencia),
    }
