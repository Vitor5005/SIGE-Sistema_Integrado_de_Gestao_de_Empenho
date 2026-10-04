from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Case, DecimalField, F, Sum, Value, When
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from empenho.models import Empenho, ItemEmpenho, OperacaoItem, SolicitacaoReforco
from licitacao.models import Ata, ItemAta


MINIMO = Decimal('1.00')


def _decimal(valor):
    try:
        return Decimal(str(valor)).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError({'valor': 'Informe uma quantidade valida.'}) from exc


def _total_operacoes(queryset):
    return queryset.aggregate(
        total=Sum(
            Case(
                When(tipo__in=['inc', 'ref'], then=F('valor')),
                When(tipo='anl', then=-F('valor')),
                default=Value(Decimal('0.00')),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
    )['total'] or Decimal('0.00')


def saldo_disponivel_ata(item_ata):
    """Quantidade do item ainda disponível na ARP para inclusões e reforços."""
    comprometido = _total_operacoes(OperacaoItem.objects.filter(item_empenho__item_ata=item_ata))
    return item_ata.quantidade_licitada - comprometido


@transaction.atomic
def registrar_operacao_item(*, item_empenho_id, tipo, valor, data):
    if tipo not in {'inc', 'ref', 'anl'}:
        raise ValidationError({'tipo': 'Tipo de operacao invalido.'})

    quantidade = _decimal(valor)
    if quantidade < MINIMO:
        raise ValidationError({'valor': 'A quantidade minima por operacao e 1,00.'})

    item_empenho = (
        ItemEmpenho.objects.select_for_update()
        .select_related('empenho', 'item_ata')
        .get(pk=item_empenho_id)
    )
    item_ata = ItemAta.objects.select_for_update().get(pk=item_empenho.item_ata_id)
    empenho = Empenho.objects.select_for_update().get(pk=item_empenho.empenho_id)
    ata = Ata.objects.select_for_update().get(pk=item_ata.ata_id)

    saldo_ata = saldo_disponivel_ata(item_ata)

    if tipo in {'inc', 'ref'}:
        if tipo == 'inc' and OperacaoItem.objects.filter(
            item_empenho=item_empenho, tipo='inc'
        ).exists():
            raise ValidationError({'tipo': 'Este item do empenho ja possui uma inclusao.'})
        if quantidade > saldo_ata:
            raise ValidationError({
                'valor': f'Saldo insuficiente na ARP. Disponivel: {saldo_ata:.2f}.'
            })
        nova_quantidade = item_empenho.quantidade_atual + quantidade
        delta_financeiro = quantidade * item_ata.valor_unitario
    else:
        comprometido_item = _total_operacoes(
            OperacaoItem.objects.filter(item_empenho=item_empenho)
        )
        limite_anulacao = min(comprometido_item, item_empenho.quantidade_atual)
        if quantidade > limite_anulacao:
            raise ValidationError({
                'valor': f'A anulacao excede o saldo disponivel do item. Disponivel: {limite_anulacao:.2f}.'
            })
        nova_quantidade = item_empenho.quantidade_atual - quantidade
        delta_financeiro = -(quantidade * item_ata.valor_unitario)

    novo_valor_empenho = (empenho.valor_total + delta_financeiro).quantize(Decimal('0.01'))
    if novo_valor_empenho < 0:
        raise ValidationError({'valor': 'A operacao produziria saldo financeiro negativo.'})

    operacao = OperacaoItem.objects.create(
        item_empenho=item_empenho,
        tipo=tipo,
        valor=quantidade,
        data=data,
        ciente_tecnico=tipo != 'ref',
    )
    item_empenho.quantidade_atual = nova_quantidade
    item_empenho.save(update_fields=['quantidade_atual'])
    empenho.valor_total = novo_valor_empenho
    empenho.save(update_fields=['valor_total'])
    saldo_financeiro_ata = Decimal('0.00')
    for item in ItemAta.objects.filter(ata=ata):
        consumido = _total_operacoes(
            OperacaoItem.objects.filter(item_empenho__item_ata=item)
        )
        saldo_item = item.quantidade_licitada - consumido
        if saldo_item < 0:
            raise ValidationError({'valor': 'A operacao produziria saldo negativo na ARP.'})
        saldo_financeiro_ata += saldo_item * item.valor_unitario
    ata.ata_saldo_total = saldo_financeiro_ata.quantize(Decimal('0.01'))
    ata.save(update_fields=['ata_saldo_total'])
    return operacao


@transaction.atomic
def solicitar_reforco(*, item_empenho_id, quantidade, justificativa, usuario):
    quantidade = _decimal(quantidade)
    if quantidade < MINIMO:
        raise ValidationError({'quantidade': 'A quantidade minima por reforco e 1,00.'})
    justificativa = str(justificativa or '').strip()
    if not justificativa:
        raise ValidationError({'justificativa': 'Informe a justificativa do reforco.'})

    item_empenho = ItemEmpenho.objects.select_related('item_ata').get(pk=item_empenho_id)
    saldo_ata = saldo_disponivel_ata(item_empenho.item_ata)
    if quantidade > saldo_ata:
        raise ValidationError({
            'quantidade': f'Saldo insuficiente na ARP. Disponivel: {saldo_ata:.2f}.'
        })

    return SolicitacaoReforco.objects.create(
        item_empenho=item_empenho,
        quantidade=quantidade,
        justificativa=justificativa,
        solicitante=usuario,
    )


def _solicitacao_pendente(solicitacao_id):
    solicitacao = SolicitacaoReforco.objects.select_for_update().get(pk=solicitacao_id)
    if solicitacao.status != SolicitacaoReforco.Status.PENDENTE:
        raise ValidationError({'status': 'Esta solicitacao ja foi respondida.'})
    return solicitacao


@transaction.atomic
def atender_solicitacao_reforco(*, solicitacao_id, usuario, resposta=''):
    """Executa o reforco pedido; o saldo da ARP e validado novamente no registro da operacao."""
    solicitacao = _solicitacao_pendente(solicitacao_id)
    operacao = registrar_operacao_item(
        item_empenho_id=solicitacao.item_empenho_id,
        tipo='ref',
        valor=solicitacao.quantidade,
        data=timezone.now(),
    )
    solicitacao.status = SolicitacaoReforco.Status.ATENDIDA
    solicitacao.operacao = operacao
    solicitacao.respondida_por = usuario
    solicitacao.resposta = str(resposta or '').strip()
    solicitacao.data_resposta = timezone.now()
    solicitacao.vista_pelo_solicitante = False
    solicitacao.save()
    return solicitacao


@transaction.atomic
def recusar_solicitacao_reforco(*, solicitacao_id, usuario, resposta):
    resposta = str(resposta or '').strip()
    if not resposta:
        raise ValidationError({'resposta': 'Informe o motivo da recusa.'})
    solicitacao = _solicitacao_pendente(solicitacao_id)
    solicitacao.status = SolicitacaoReforco.Status.RECUSADA
    solicitacao.respondida_por = usuario
    solicitacao.resposta = resposta
    solicitacao.data_resposta = timezone.now()
    solicitacao.vista_pelo_solicitante = False
    solicitacao.save()
    return solicitacao
