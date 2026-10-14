from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from cardapio.models import Cardapio, ItemCardapio
from estoque.models import Estoque
from utils.estoque_services import registrar_devolucao_cardapio, registrar_saida_cardapio

ZERO = Decimal('0.000')
TRES_CASAS = Decimal('0.001')


def _quantidade(valor, campo):
    try:
        quantidade = Decimal(str(valor)).quantize(TRES_CASAS)
    except Exception:
        raise ValidationError({campo: 'Informe uma quantidade numérica.'})
    if quantidade < ZERO:
        raise ValidationError({campo: 'A quantidade não pode ser negativa.'})
    return quantidade


def _referencia(cardapio):
    return f'Cardápio nº {cardapio.pk} - {cardapio.get_refeicao_display()} de {cardapio.data:%d/%m/%Y}'


def _retirar(item, quantidade, usuario, observacao):
    try:
        registrar_saida_cardapio(
            item_cardapio=item, quantidade=quantidade, usuario=usuario, observacao=observacao,
        )
    except ValidationError:
        raise ValidationError({
            'itens': [f'{item.item_generico.descricao}: saldo em estoque insuficiente para retirar '
                      f'{quantidade.normalize():f} {item.item_generico.unidade_medida}.'],
        })


def _bloquear(cardapio_id, status_permitidos, mensagem):
    cardapio = Cardapio.objects.select_for_update().get(pk=cardapio_id)
    if cardapio.status not in status_permitidos:
        raise ValidationError({'status': mensagem})
    return cardapio


def quantidades_reservadas(excluir_cardapio_id=None):
    """Soma, por gênero, o planejado em cardápios enviados que ainda aguardam aprovação."""
    itens = ItemCardapio.objects.filter(cardapio__status=Cardapio.Status.ENVIADO)
    if excluir_cardapio_id:
        itens = itens.exclude(cardapio_id=excluir_cardapio_id)
    return {
        linha['item_generico_id']: linha['total']
        for linha in itens.values('item_generico_id').annotate(total=Sum('quantidade_planejada'))
    }


def disponibilidade(excluir_cardapio_id=None):
    """Saldo físico, reservado e disponível de cada gênero com registro de estoque."""
    reservado = quantidades_reservadas(excluir_cardapio_id)
    dados = []
    for estoque in Estoque.objects.select_related('item_generico').order_by('item_generico__descricao'):
        genero = estoque.item_generico
        reservado_item = reservado.get(genero.id, ZERO)
        dados.append({
            'item_generico_id': genero.id,
            'catmat': genero.catmat,
            'descricao': genero.descricao,
            'unidade_medida': genero.unidade_medida,
            'categoria': genero.categoria,
            'conteudo_embalagem': genero.conteudo_embalagem,
            'unidade_embalagem': genero.unidade_embalagem,
            'saldo_atual': estoque.saldo_atual,
            'reservado': reservado_item,
            'disponivel': max(estoque.saldo_atual - reservado_item, ZERO),
        })
    return dados


def faltas_de_saldo(planejado, generos, excluir_cardapio_id=None, bloquear=False):
    """Mensagens dos gêneros sem saldo ou com quantidade acima do disponível.

    `planejado` soma por gênero o que o cardápio pretende usar; `generos` mapeia o id para o
    ItemGenerico (para as mensagens). Com `bloquear`, trava os saldos até o fim da transação.
    """
    estoques = Estoque.objects.filter(item_generico_id__in=planejado)
    if bloquear:
        estoques = estoques.select_for_update()
    saldos = {estoque.item_generico_id: estoque.saldo_atual for estoque in estoques}
    reservado = quantidades_reservadas(excluir_cardapio_id=excluir_cardapio_id)

    faltas = []
    for item_id, quantidade in planejado.items():
        genero = generos[item_id]
        disponivel = max(saldos.get(item_id, ZERO) - reservado.get(item_id, ZERO), ZERO)
        if disponivel <= ZERO:
            faltas.append(f'{genero.descricao}: sem saldo disponível em estoque.')
        elif quantidade > disponivel:
            faltas.append(
                f'{genero.descricao}: planejado {quantidade.normalize():f} {genero.unidade_medida}, '
                f'disponível {disponivel.normalize():f} {genero.unidade_medida}.'
            )
    return faltas


def _validar_disponibilidade(cardapio):
    planejado = defaultdict(lambda: ZERO)
    generos = {}
    for item in cardapio.itens.select_related('item_generico'):
        planejado[item.item_generico_id] += item.quantidade_planejada
        generos[item.item_generico_id] = item.item_generico

    # Bloqueia os saldos envolvidos para que dois envios simultâneos não reservem o mesmo saldo.
    faltas = faltas_de_saldo(planejado, generos, excluir_cardapio_id=cardapio.pk, bloquear=True)
    if faltas:
        raise ValidationError({'itens': faltas})


@transaction.atomic
def enviar(*, cardapio_id, usuario):
    cardapio = _bloquear(
        cardapio_id, Cardapio.STATUS_EDITAVEIS, 'Somente rascunhos ou cardápios recusados podem ser enviados.',
    )
    if not cardapio.itens.exists():
        raise ValidationError({'itens': 'Adicione ao menos um gênero ao detalhamento antes de enviar.'})
    _validar_disponibilidade(cardapio)

    cardapio.status = Cardapio.Status.ENVIADO
    cardapio.enviado_em = timezone.now()
    cardapio.motivo_recusa = ''
    cardapio.save(update_fields=['status', 'enviado_em', 'motivo_recusa', 'atualizado_em'])
    return cardapio


@transaction.atomic
def recusar(*, cardapio_id, motivo, usuario):
    cardapio = _bloquear(cardapio_id, [Cardapio.Status.ENVIADO], 'Somente cardápios enviados podem ser recusados.')
    motivo = (motivo or '').strip()
    if not motivo:
        raise ValidationError({'motivo': 'Informe o motivo da recusa.'})

    cardapio.status = Cardapio.Status.RECUSADO
    cardapio.motivo_recusa = motivo
    cardapio.save(update_fields=['status', 'motivo_recusa', 'atualizado_em'])
    return cardapio


@transaction.atomic
def aprovar(*, cardapio_id, quantidades, usuario):
    """Registra a retirada do estoque com as quantidades liberadas pelo Estoquista.

    `quantidades` mapeia o id do item do cardápio para a quantidade liberada; um item
    ausente é liberado integralmente. A liberada pode ser menor que a planejada (inclusive 0),
    nunca maior, e nunca acima do saldo físico.
    """
    cardapio = _bloquear(cardapio_id, [Cardapio.Status.ENVIADO], 'Somente cardápios enviados podem ser aprovados.')
    itens = list(cardapio.itens.select_related('item_generico'))
    ids_validos = {item.id for item in itens}
    desconhecidos = set(quantidades) - ids_validos
    if desconhecidos:
        raise ValidationError({'quantidades': 'Há itens que não pertencem a este cardápio.'})

    referencia = _referencia(cardapio)
    for item in itens:
        liberada = _quantidade(quantidades.get(item.id, item.quantidade_planejada), f'item {item.id}')
        if liberada > item.quantidade_planejada:
            raise ValidationError({
                'quantidades': f'{item.item_generico.descricao}: a quantidade liberada não pode ser maior que a planejada.',
            })
        item.quantidade_liberada = liberada
        item.save(update_fields=['quantidade_liberada'])
        if liberada > ZERO:
            _retirar(item, liberada, usuario, f'Retirada para o {referencia}.')

    cardapio.status = Cardapio.Status.APROVADO
    cardapio.aprovado_por = usuario
    cardapio.aprovado_em = timezone.now()
    cardapio.motivo_recusa = ''
    cardapio.save(update_fields=['status', 'aprovado_por', 'aprovado_em', 'motivo_recusa', 'atualizado_em'])
    return cardapio


@transaction.atomic
def informar_consumo(*, cardapio_id, quantidades, usuario):
    """A Nutricionista informa quanto de cada item foi realmente usado no preparo."""
    cardapio = _bloquear(
        cardapio_id,
        [Cardapio.Status.APROVADO, Cardapio.Status.CONSUMO_INFORMADO],
        'O consumo só pode ser informado após a aprovação da retirada.',
    )
    itens = list(cardapio.itens.all())
    faltantes = [item.id for item in itens if item.id not in quantidades]
    if faltantes:
        raise ValidationError({'quantidades': 'Informe o consumo real de todos os itens do cardápio.'})

    for item in itens:
        item.quantidade_consumida = _quantidade(quantidades[item.id], f'item {item.id}')
        item.save(update_fields=['quantidade_consumida'])

    cardapio.status = Cardapio.Status.CONSUMO_INFORMADO
    cardapio.consumo_informado_em = timezone.now()
    cardapio.motivo_recusa = ''
    cardapio.save(update_fields=['status', 'consumo_informado_em', 'motivo_recusa', 'atualizado_em'])
    return cardapio


@transaction.atomic
def devolver_consumo(*, cardapio_id, motivo, usuario):
    """O Estoquista discorda do consumo informado e devolve para a Nutricionista corrigir."""
    cardapio = _bloquear(
        cardapio_id, [Cardapio.Status.CONSUMO_INFORMADO], 'Não há consumo aguardando confirmação.',
    )
    motivo = (motivo or '').strip()
    if not motivo:
        raise ValidationError({'motivo': 'Informe o motivo da devolução.'})

    cardapio.status = Cardapio.Status.APROVADO
    cardapio.motivo_recusa = motivo
    cardapio.save(update_fields=['status', 'motivo_recusa', 'atualizado_em'])
    return cardapio


@transaction.atomic
def confirmar_consumo(*, cardapio_id, usuario):
    """Acerta o estoque pela diferença entre o liberado e o consumido de cada item.

    Consumiu menos: a sobra volta ao estoque (DEVOLUCAO_PREPARO).
    Consumiu mais: o excedente é retirado (SAIDA_PRODUCAO), limitado ao saldo físico.
    """
    cardapio = _bloquear(
        cardapio_id, [Cardapio.Status.CONSUMO_INFORMADO], 'Não há consumo aguardando confirmação.',
    )
    referencia = _referencia(cardapio)
    for item in cardapio.itens.select_related('item_generico'):
        diferenca = (item.quantidade_consumida or ZERO) - (item.quantidade_liberada or ZERO)
        if diferenca > ZERO:
            _retirar(item, diferenca, usuario, f'Consumo acima do liberado no {referencia}.')
        elif diferenca < ZERO:
            registrar_devolucao_cardapio(
                item_cardapio=item,
                quantidade=-diferenca,
                usuario=usuario,
                observacao=f'Sobra devolvida do {referencia}.',
            )

    cardapio.status = Cardapio.Status.FINALIZADO
    cardapio.finalizado_por = usuario
    cardapio.finalizado_em = timezone.now()
    cardapio.save(update_fields=['status', 'finalizado_por', 'finalizado_em', 'atualizado_em'])
    return cardapio
