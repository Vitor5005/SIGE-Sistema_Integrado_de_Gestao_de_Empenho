from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from empenho.models import Empenho, ItemEmpenho
from entrega.models import ItemOrdem, OrdemEntrega
from utils.pendencias import sincronizar_pendencias
from estoque.models import Estoque, Inventario, ItemInventario, MovimentacaoEstoque


ZERO = Decimal('0.000')


def _decimal(valor, campo='quantidade'):
    try:
        return Decimal(str(valor)).quantize(Decimal('0.001'))
    except Exception as exc:
        raise ValidationError({campo: 'Informe um valor numérico válido.'}) from exc


def _justificativa(valor):
    texto = str(valor or '').strip()
    if not texto:
        raise ValidationError({'justificativa': 'A justificativa é obrigatória.'})
    return texto


def _estoque_bloqueado(item_generico_id):
    Estoque.objects.get_or_create(item_generico_id=item_generico_id)
    return Estoque.objects.select_for_update().select_related('item_generico').get(
        item_generico_id=item_generico_id
    )


def _registrar_movimentacao(
    *, item_generico_id, tipo, sentido, quantidade, usuario, data_hora,
    observacao='', item_ordem=None, item_inventario=None, movimentacao_estornada=None,
):
    quantidade = _decimal(quantidade)
    if quantidade <= ZERO:
        raise ValidationError({'quantidade': 'A quantidade deve ser maior que zero.'})

    estoque = _estoque_bloqueado(item_generico_id)
    delta = quantidade if sentido == MovimentacaoEstoque.Sentido.ENTRADA else -quantidade
    novo_saldo = (estoque.saldo_atual + delta).quantize(Decimal('0.001'))
    if novo_saldo < ZERO:
        raise ValidationError({'quantidade': 'A quantidade informada excede o saldo em estoque.'})

    movimento = MovimentacaoEstoque.objects.create(
        estoque=estoque,
        tipo=tipo,
        sentido=sentido,
        quantidade=quantidade,
        saldo_resultante=novo_saldo,
        data_hora=data_hora,
        observacao=observacao or None,
        item_ordem=item_ordem,
        item_inventario=item_inventario,
        movimentacao_estornada=movimentacao_estornada,
        usuario=usuario,
        papel=usuario.papel,
    )
    Estoque.objects.filter(pk=estoque.pk).update(
        saldo_atual=novo_saldo,
        data_atualizacao=timezone.now(),
    )
    return movimento


@transaction.atomic
def registrar_saida(*, item_generico_id, quantidade, tipo_saida, justificativa, usuario, data_hora=None):
    tipos = {
        'PRODUCAO': MovimentacaoEstoque.Tipo.SAIDA_PRODUCAO,
        'DOACAO': MovimentacaoEstoque.Tipo.SAIDA_DOACAO,
        'PERDA': MovimentacaoEstoque.Tipo.SAIDA_PERDA,
    }
    if tipo_saida not in tipos:
        raise ValidationError({'tipo_saida': 'Tipo de saída inválido.'})
    return _registrar_movimentacao(
        item_generico_id=item_generico_id,
        tipo=tipos[tipo_saida],
        sentido=MovimentacaoEstoque.Sentido.SAIDA,
        quantidade=quantidade,
        usuario=usuario,
        data_hora=data_hora or timezone.now(),
        observacao=_justificativa(justificativa),
    )


@transaction.atomic
def registrar_carga_inicial(*, item_generico_id, quantidade, justificativa, usuario, data_hora=None):
    estoque = _estoque_bloqueado(item_generico_id)
    if MovimentacaoEstoque.objects.filter(
        estoque=estoque,
        tipo=MovimentacaoEstoque.Tipo.CARGA_INICIAL,
    ).exists():
        raise ValidationError({'item_generico': 'Este gênero já possui carga inicial.'})

    momento = data_hora or timezone.now()
    inventario = Inventario.objects.create(
        tipo=Inventario.Tipo.CARGA_INICIAL,
        status=Inventario.Status.FINALIZADO,
        data_contagem=momento,
        data_finalizacao=momento,
        observacao=_justificativa(justificativa),
        usuario=usuario,
    )
    item = ItemInventario.objects.create(
        inventario=inventario,
        estoque=estoque,
        saldo_sistema=estoque.saldo_atual,
        quantidade_contada=_decimal(quantidade),
    )
    return _registrar_movimentacao(
        item_generico_id=item_generico_id,
        tipo=MovimentacaoEstoque.Tipo.CARGA_INICIAL,
        sentido=MovimentacaoEstoque.Sentido.ENTRADA,
        quantidade=quantidade,
        usuario=usuario,
        data_hora=momento,
        observacao=inventario.observacao,
        item_inventario=item,
    )


@transaction.atomic
def registrar_ajuste(*, item_generico_id, quantidade_contada, justificativa, usuario, data_hora=None):
    """Inventário: recebe o que foi contado na prateleira e lança a diferença para o saldo do sistema."""
    quantidade_contada = _decimal(quantidade_contada, 'quantidade_contada')
    if quantidade_contada < ZERO:
        raise ValidationError({'quantidade_contada': 'A quantidade contada não pode ser negativa.'})

    estoque = _estoque_bloqueado(item_generico_id)
    ajuste = quantidade_contada - estoque.saldo_atual
    if ajuste == ZERO:
        raise ValidationError({
            'quantidade_contada': 'A contagem confere com o saldo do sistema; não há diferença a ajustar.'
        })

    momento = data_hora or timezone.now()
    inventario = Inventario.objects.create(
        tipo=Inventario.Tipo.PERIODICO,
        status=Inventario.Status.FINALIZADO,
        data_contagem=momento,
        data_finalizacao=momento,
        observacao=_justificativa(justificativa),
        usuario=usuario,
    )
    item = ItemInventario.objects.create(
        inventario=inventario,
        estoque=estoque,
        saldo_sistema=estoque.saldo_atual,
        quantidade_contada=quantidade_contada,
    )
    positivo = ajuste > ZERO
    return _registrar_movimentacao(
        item_generico_id=item_generico_id,
        tipo=(MovimentacaoEstoque.Tipo.AJUSTE_POSITIVO if positivo else MovimentacaoEstoque.Tipo.AJUSTE_NEGATIVO),
        sentido=(MovimentacaoEstoque.Sentido.ENTRADA if positivo else MovimentacaoEstoque.Sentido.SAIDA),
        quantidade=abs(ajuste),
        usuario=usuario,
        data_hora=momento,
        observacao=inventario.observacao,
        item_inventario=item,
    )


@transaction.atomic
def estornar_movimentacao(*, movimentacao_id, justificativa, usuario, data_hora=None):
    original = MovimentacaoEstoque.objects.select_for_update().select_related('estoque').get(pk=movimentacao_id)
    if original.tipo == MovimentacaoEstoque.Tipo.ESTORNO:
        raise ValidationError({'movimentacao': 'Não é permitido estornar um estorno.'})
    if MovimentacaoEstoque.objects.filter(movimentacao_estornada=original).exists():
        raise ValidationError({'movimentacao': 'Esta movimentação já foi estornada.'})

    sentido = (
        MovimentacaoEstoque.Sentido.SAIDA
        if original.sentido == MovimentacaoEstoque.Sentido.ENTRADA
        else MovimentacaoEstoque.Sentido.ENTRADA
    )
    return _registrar_movimentacao(
        item_generico_id=original.estoque.item_generico_id,
        tipo=MovimentacaoEstoque.Tipo.ESTORNO,
        sentido=sentido,
        quantidade=original.quantidade,
        usuario=usuario,
        data_hora=data_hora or timezone.now(),
        observacao=_justificativa(justificativa),
        movimentacao_estornada=original,
    )


@transaction.atomic
def registrar_recebimento(*, ordem_id, itens_recebidos, usuario, data_entrada=None):
    ordem = OrdemEntrega.objects.select_for_update().select_related('empenho').get(pk=ordem_id)
    if ordem.status == 'con':
        raise ValidationError({'ordem': 'Esta ordem de entrega já foi concluída.'})

    itens_ordem = list(
        ItemOrdem.objects.select_for_update()
        .select_related('item_empenho__item_ata__item_generico')
        .filter(ordem_entrega=ordem)
    )
    por_id = {}
    for recebido in itens_recebidos:
        item_id = recebido.get('item_ordem_id')
        if item_id in por_id:
            raise ValidationError({'itens': 'O mesmo item da ordem foi informado mais de uma vez.'})
        por_id[item_id] = recebido
    ids_validos = {item.pk for item in itens_ordem}
    if not por_id or not set(por_id).issubset(ids_validos):
        raise ValidationError({'itens': 'Informe itens pertencentes à ordem de entrega.'})

    momento = data_entrada or timezone.now()
    valor_deste_recebimento = Decimal('0.00')
    movimentos = []

    for item_ordem in itens_ordem:
        recebido = por_id.get(item_ordem.pk)
        quantidade = _decimal(recebido.get('quantidade_recebida'), 'quantidade_recebida') if recebido else ZERO
        solicitada = _decimal(item_ordem.quantidade_solicitada)
        entregue_antes = _decimal(item_ordem.quantidade_entregue)
        pendente_antes = solicitada - entregue_antes
        if recebido and quantidade <= ZERO:
            raise ValidationError({'quantidade_recebida': 'A quantidade recebida deve ser maior que zero.'})
        if quantidade > pendente_antes:
            raise ValidationError({'quantidade_recebida': 'A quantidade recebida não pode exceder a quantidade pendente.'})
        if recebido and quantidade < pendente_antes and not str(recebido.get('observacao') or '').strip():
            raise ValidationError({'observacao': 'Informe o motivo da entrega parcial e da quantidade pendente.'})

        item_ordem.quantidade_entregue = entregue_antes + quantidade
        item_ordem.observacao = (recebido or {}).get('observacao') or item_ordem.observacao
        item_ordem.save(update_fields=['quantidade_entregue', 'observacao'])

        if quantidade > ZERO:
            movimento = _registrar_movimentacao(
                item_generico_id=item_ordem.item_empenho.item_ata.item_generico_id,
                tipo=MovimentacaoEstoque.Tipo.ENTRADA_FORNECEDOR,
                sentido=MovimentacaoEstoque.Sentido.ENTRADA,
                quantidade=quantidade,
                usuario=usuario,
                data_hora=momento,
                item_ordem=item_ordem,
            )
            movimentos.append(movimento)
            valor_deste_recebimento += quantidade * item_ordem.item_empenho.item_ata.valor_unitario

    empenho = Empenho.objects.select_for_update().get(pk=ordem.empenho_id)
    empenho.saldo_utilizado = (empenho.saldo_utilizado + valor_deste_recebimento).quantize(Decimal('0.01'))
    empenho.save(update_fields=['saldo_utilizado'])

    itens_atualizados = list(
        ItemOrdem.objects.select_related('item_empenho__item_ata').filter(ordem_entrega=ordem)
    )
    todos_concluidos = all(
        item.quantidade_entregue >= item.quantidade_solicitada
        for item in itens_atualizados
    )
    ordem.status = 'con' if todos_concluidos else 'par'
    ordem.data_entrega = momento if todos_concluidos else None
    ordem.valor_total_executado = sum(
        item.quantidade_entregue * item.item_empenho.item_ata.valor_unitario
        for item in itens_atualizados
    ).quantize(Decimal('0.01'))
    ordem.save(update_fields=['status', 'data_entrega', 'valor_total_executado'])
    sincronizar_pendencias(
        ordem=ordem,
        itens_ordem=itens_atualizados,
        recebidos_por_id=por_id,
        usuario=usuario,
    )
    return ordem, movimentos

