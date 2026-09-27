from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Case, DecimalField, F, Sum, Value, When
from rest_framework.exceptions import ValidationError

from empenho.models import Empenho, ItemEmpenho, OperacaoItem
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

    operacoes_ata = OperacaoItem.objects.filter(item_empenho__item_ata=item_ata)
    comprometido_ata = _total_operacoes(operacoes_ata)
    saldo_ata = item_ata.quantidade_licitada - comprometido_ata

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
