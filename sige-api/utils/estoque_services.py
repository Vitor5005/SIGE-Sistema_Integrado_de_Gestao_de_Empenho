from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError

from empenho.models import Empenho, ItemEmpenho
from entrega.models import ItemOrdem, OrdemEntrega
from utils.pendencias import sincronizar_pendencias
from estoque.models import (
    Estoque,
    Inventario,
    ItemInventario,
    LoteEstoque,
    MovimentacaoEstoque,
    MovimentacaoLote,
)


ZERO = Decimal('0.000')
FUSO_ESTOQUE = ZoneInfo('America/Rio_Branco')


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


def _lote_legado_bloqueado(estoque):
    LoteEstoque.objects.get_or_create(
        estoque=estoque,
        numero_lote=LoteEstoque.NUMERO_LOTE_LEGADO,
        defaults={
            'data_validade': None,
            'saldo_atual': estoque.saldo_atual,
            'legado': True,
        },
    )
    lote = LoteEstoque.objects.select_for_update().get(
        estoque=estoque,
        numero_lote=LoteEstoque.NUMERO_LOTE_LEGADO,
    )
    if not lote.legado or lote.data_validade is not None:
        raise ValidationError({
            'estoque': 'O lote legado do estoque está inconsistente.',
        })
    return lote


def _validar_consistencia_lotes(estoque):
    total_lotes = (
        LoteEstoque.objects
        .filter(estoque_id=estoque.id)
        .aggregate(total=Sum('saldo_atual'))['total']
        or ZERO
    ).quantize(Decimal('0.001'))
    if total_lotes != estoque.saldo_atual:
        raise ValidationError({
            'estoque': 'Inconsistência entre o saldo consolidado e os saldos dos lotes.',
        })


def _numero_lote(valor):
    texto = str(valor or '').strip()
    if not texto:
        raise ValidationError({'numero_lote': 'Informe o número do lote.'})
    if texto.casefold() == LoteEstoque.NUMERO_LOTE_LEGADO.casefold():
        raise ValidationError({
            'numero_lote': (
                'O identificador LEGADO é reservado para saldos anteriores ao controle de lotes.'
            ),
        })
    if len(texto) > 100:
        raise ValidationError({
            'numero_lote': 'O número do lote deve possuir no máximo 100 caracteres.',
        })
    return texto


def _data_validade(valor):
    if isinstance(valor, datetime):
        data_validade = None
    elif isinstance(valor, date):
        data_validade = valor
    elif isinstance(valor, str):
        try:
            data_validade = parse_date(valor)
        except (TypeError, ValueError):
            data_validade = None
    else:
        data_validade = None

    if data_validade is None:
        raise ValidationError({'data_validade': 'Informe uma data de validade válida.'})
    return data_validade


def _data_local(momento):
    if isinstance(momento, datetime):
        if timezone.is_aware(momento):
            return timezone.localtime(momento, FUSO_ESTOQUE).date()
        return momento.date()
    if isinstance(momento, date):
        return momento
    raise ValidationError({'data_entrada': 'Informe uma data de entrada válida.'})


def _data_referencia_lotes(data_referencia=None):
    if data_referencia is None:
        return timezone.localtime(timezone.now(), FUSO_ESTOQUE).date()
    return _data_local(data_referencia)


def lote_vencido(lote, data_referencia=None):
    if lote.legado:
        return False
    if lote.data_validade is None:
        return False
    return lote.data_validade < _data_referencia_lotes(data_referencia)


def saldo_utilizavel_estoque(estoque, data_referencia=None):
    referencia = _data_referencia_lotes(data_referencia)
    total = ZERO
    for lote in LoteEstoque.objects.filter(estoque=estoque, saldo_atual__gt=ZERO):
        if lote.legado or not lote_vencido(lote, referencia):
            total = (total + _decimal(lote.saldo_atual)).quantize(Decimal('0.001'))
    return total.quantize(Decimal('0.001'))


def _lote_recebimento_bloqueado(*, estoque, numero_lote, data_validade):
    numero_lote = _numero_lote(numero_lote)
    data_validade = _data_validade(data_validade)
    lote = (
        LoteEstoque.objects.select_for_update()
        .filter(estoque=estoque, numero_lote__iexact=numero_lote)
        .first()
    )
    if lote:
        if lote.legado:
            raise ValidationError({
                'numero_lote': (
                    'O identificador LEGADO é reservado para saldos anteriores ao controle de lotes.'
                ),
            })
        if lote.data_validade != data_validade:
            raise ValidationError({
                'data_validade': (
                    f'O lote {numero_lote} já está registrado com outra data de validade.'
                ),
            })
        return lote

    lote = LoteEstoque(
        estoque=estoque,
        numero_lote=numero_lote,
        data_validade=data_validade,
        saldo_atual=ZERO,
        legado=False,
    )
    lote.full_clean()
    lote.save()
    return lote


def _resolver_alocacoes_lote(*, estoque, quantidade, sentido, alocacoes_lote):
    if not alocacoes_lote:
        raise ValidationError({'lotes': 'Informe ao menos um lote para a movimentação.'})

    alocacoes = []
    lote_ids = set()
    total = ZERO
    for alocacao in alocacoes_lote:
        if not isinstance(alocacao, dict) or alocacao.get('lote_id') is None:
            raise ValidationError({'lotes': 'Informe um lote válido para a movimentação.'})

        try:
            lote = LoteEstoque.objects.select_for_update().get(pk=alocacao['lote_id'])
        except (LoteEstoque.DoesNotExist, TypeError, ValueError) as exc:
            raise ValidationError({'lotes': 'Informe um lote válido para a movimentação.'}) from exc
        if lote.estoque_id != estoque.id:
            raise ValidationError({'lotes': 'O lote informado não pertence ao mesmo estoque.'})
        if lote.pk in lote_ids:
            raise ValidationError({'lotes': 'O mesmo lote foi informado mais de uma vez para a movimentação.'})

        quantidade_lote = _decimal(alocacao.get('quantidade'))
        if quantidade_lote <= ZERO:
            raise ValidationError({'quantidade': 'A quantidade deve ser maior que zero.'})

        lote_ids.add(lote.pk)
        total = (total + quantidade_lote).quantize(Decimal('0.001'))
        alocacoes.append({'lote': lote, 'quantidade': quantidade_lote})

    if total != quantidade:
        raise ValidationError({
            'lotes': (
                'A soma das quantidades dos lotes deve ser igual à quantidade total da movimentação.'
            ),
        })
    return alocacoes


def _alocacoes_saida_compativel(*, estoque, quantidade):
    lotes = list(
        LoteEstoque.objects.select_for_update()
        .filter(estoque=estoque, saldo_atual__gt=ZERO)
    )
    lotes.sort(key=lambda lote: (
        0 if lote.legado else 1,
        lote.data_validade if lote.data_validade is not None else date.max,
        lote.id,
    ))

    restante = quantidade
    alocacoes = []
    for lote in lotes:
        if restante <= ZERO:
            break
        quantidade_lote = min(_decimal(lote.saldo_atual), restante)
        if quantidade_lote > ZERO:
            alocacoes.append({'lote': lote, 'quantidade': quantidade_lote})
            restante = (restante - quantidade_lote).quantize(Decimal('0.001'))

    if restante > ZERO:
        raise ValidationError({'quantidade': 'A quantidade informada excede o saldo em estoque.'})
    return alocacoes


def _alocacoes_saida_fefo(*, estoque, quantidade, data_referencia):
    referencia = _data_referencia_lotes(data_referencia)
    lotes = list(
        LoteEstoque.objects.select_for_update()
        .filter(estoque=estoque, saldo_atual__gt=ZERO)
    )
    lotes_reais = sorted(
        (
            lote for lote in lotes
            if not lote.legado and not lote_vencido(lote, referencia)
        ),
        key=lambda lote: (lote.data_validade, lote.id),
    )
    lotes_legado = sorted(
        (lote for lote in lotes if lote.legado),
        key=lambda lote: lote.id,
    )

    restante = quantidade
    alocacoes = []
    for lote in [*lotes_reais, *lotes_legado]:
        if restante <= ZERO:
            break
        quantidade_lote = min(_decimal(lote.saldo_atual), restante)
        if quantidade_lote > ZERO:
            alocacoes.append({'lote': lote, 'quantidade': quantidade_lote})
            restante = (restante - quantidade_lote).quantize(Decimal('0.001'))

    if restante > ZERO:
        saldo_fisico = _decimal(estoque.saldo_atual)
        saldo_utilizavel = saldo_utilizavel_estoque(estoque, referencia)
        if saldo_fisico >= quantidade and saldo_utilizavel < quantidade:
            raise ValidationError({
                'quantidade': (
                    'H\u00e1 saldo f\u00edsico em estoque, mas a quantidade dispon\u00edvel para uso \u00e9 insuficiente '
                    'porque existem lotes vencidos.'
                ),
            })
        raise ValidationError({'quantidade': 'A quantidade informada excede o saldo em estoque.'})
    return alocacoes


@transaction.atomic
def _registrar_movimentacao(
    *, item_generico_id, tipo, sentido, quantidade, usuario, data_hora,
    observacao='', item_ordem=None, item_inventario=None, movimentacao_estornada=None,
    item_cardapio=None, alocacoes_lote=None, usar_fefo=False, data_referencia_lotes=None,
):
    quantidade = _decimal(quantidade)
    if quantidade <= ZERO:
        raise ValidationError({'quantidade': 'A quantidade deve ser maior que zero.'})

    estoque = _estoque_bloqueado(item_generico_id)
    _validar_consistencia_lotes(estoque)

    if alocacoes_lote is not None:
        alocacoes = _resolver_alocacoes_lote(
            estoque=estoque,
            quantidade=quantidade,
            sentido=sentido,
            alocacoes_lote=alocacoes_lote,
        )
    elif sentido == MovimentacaoEstoque.Sentido.ENTRADA:
        lote = _lote_legado_bloqueado(estoque)
        alocacoes = [{'lote': lote, 'quantidade': quantidade}]
    elif usar_fefo:
        alocacoes = _alocacoes_saida_fefo(
            estoque=estoque,
            quantidade=quantidade,
            data_referencia=(
                data_referencia_lotes
                if data_referencia_lotes is not None
                else _data_local(data_hora)
            ),
        )
    else:
        alocacoes = _alocacoes_saida_compativel(estoque=estoque, quantidade=quantidade)

    delta = quantidade if sentido == MovimentacaoEstoque.Sentido.ENTRADA else -quantidade
    novo_saldo = (estoque.saldo_atual + delta).quantize(Decimal('0.001'))
    if novo_saldo < ZERO:
        raise ValidationError({'quantidade': 'A quantidade informada excede o saldo em estoque.'})

    novos_saldos_lote = []
    for alocacao in alocacoes:
        delta_lote = (
            alocacao['quantidade']
            if sentido == MovimentacaoEstoque.Sentido.ENTRADA
            else -alocacao['quantidade']
        )
        novo_saldo_lote = (alocacao['lote'].saldo_atual + delta_lote).quantize(Decimal('0.001'))
        if novo_saldo_lote < ZERO:
            raise ValidationError({'quantidade': 'A quantidade informada excede o saldo em estoque.'})
        novos_saldos_lote.append((alocacao['lote'], alocacao['quantidade'], novo_saldo_lote))

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
        item_cardapio=item_cardapio,
        usuario=usuario,
        papel=usuario.papel,
    )
    agora = timezone.now()
    Estoque.objects.filter(pk=estoque.pk).update(
        saldo_atual=novo_saldo,
        data_atualizacao=agora,
    )
    estoque.saldo_atual = novo_saldo
    for lote, quantidade_lote, novo_saldo_lote in novos_saldos_lote:
        LoteEstoque.objects.filter(pk=lote.pk).update(
            saldo_atual=novo_saldo_lote,
            data_atualizacao=agora,
        )
        MovimentacaoLote.objects.create(
            movimentacao=movimento,
            lote=lote,
            quantidade=quantidade_lote,
            saldo_lote_resultante=novo_saldo_lote,
        )
        lote.saldo_atual = novo_saldo_lote
    _validar_consistencia_lotes(estoque)
    return movimento


@transaction.atomic
def registrar_saida(
    *, item_generico_id, quantidade, tipo_saida, justificativa, usuario, data_hora=None, lote_id=None,
):
    tipos = {
        'PRODUCAO': MovimentacaoEstoque.Tipo.SAIDA_PRODUCAO,
        'DOACAO': MovimentacaoEstoque.Tipo.SAIDA_DOACAO,
        'PERDA': MovimentacaoEstoque.Tipo.SAIDA_PERDA,
    }
    if tipo_saida not in tipos:
        raise ValidationError({'tipo_saida': 'Tipo de saída inválido.'})
    momento = data_hora or timezone.now()
    if tipo_saida == 'PERDA':
        if lote_id is None:
            raise ValidationError({
                'lote_id': 'Selecione o lote que est\u00e1 sendo baixado por perda ou vencimento.',
            })
        alocacoes_lote = [{'lote_id': lote_id, 'quantidade': quantidade}]
        usar_fefo = False
    else:
        if lote_id is not None:
            raise ValidationError({
                'lote_id': 'O lote s\u00f3 deve ser informado para sa\u00eddas por perda ou vencimento.',
            })
        alocacoes_lote = None
        usar_fefo = True

    return _registrar_movimentacao(
        item_generico_id=item_generico_id,
        tipo=tipos[tipo_saida],
        sentido=MovimentacaoEstoque.Sentido.SAIDA,
        quantidade=quantidade,
        usuario=usuario,
        data_hora=momento,
        observacao=_justificativa(justificativa),
        alocacoes_lote=alocacoes_lote,
        usar_fefo=usar_fefo,
        data_referencia_lotes=_data_local(momento) if usar_fefo else None,
    )


def registrar_saida_cardapio(*, item_cardapio, quantidade, usuario, observacao):
    """Retira do estoque o que foi liberado (ou consumido além do liberado) para um cardápio."""
    return _registrar_movimentacao(
        item_generico_id=item_cardapio.item_generico_id,
        tipo=MovimentacaoEstoque.Tipo.SAIDA_PRODUCAO,
        sentido=MovimentacaoEstoque.Sentido.SAIDA,
        quantidade=quantidade,
        usuario=usuario,
        data_hora=timezone.now(),
        observacao=observacao,
        item_cardapio=item_cardapio,
        usar_fefo=True,
        data_referencia_lotes=item_cardapio.cardapio.data,
    )


def _alocacoes_devolucao_cardapio(*, item_cardapio, quantidade):
    quantidade = _decimal(quantidade)
    retiradas = []
    devolvido_por_lote = defaultdict(lambda: ZERO)
    for alocacao in (
        MovimentacaoLote.objects.select_for_update()
        .select_related('lote', 'movimentacao')
        .filter(movimentacao__item_cardapio=item_cardapio)
        .order_by('movimentacao__data_hora', 'movimentacao_id', 'id')
    ):
        movimento = alocacao.movimentacao
        if (
            movimento.tipo == MovimentacaoEstoque.Tipo.SAIDA_PRODUCAO
            and movimento.sentido == MovimentacaoEstoque.Sentido.SAIDA
        ):
            retiradas.append(alocacao)
        elif (
            movimento.tipo == MovimentacaoEstoque.Tipo.DEVOLUCAO_PREPARO
            and movimento.sentido == MovimentacaoEstoque.Sentido.ENTRADA
        ):
            devolvido_por_lote[alocacao.lote_id] = (
                devolvido_por_lote[alocacao.lote_id] + _decimal(alocacao.quantidade)
            ).quantize(Decimal('0.001'))

    retirado_por_lote = defaultdict(lambda: ZERO)
    for alocacao in retiradas:
        retirado_por_lote[alocacao.lote_id] = (
            retirado_por_lote[alocacao.lote_id] + _decimal(alocacao.quantidade)
        ).quantize(Decimal('0.001'))

    restante_por_lote = {
        lote_id: max(retirado - devolvido_por_lote[lote_id], ZERO)
        for lote_id, retirado in retirado_por_lote.items()
    }
    saldo_retirado = sum(restante_por_lote.values(), ZERO).quantize(Decimal('0.001'))
    if quantidade > saldo_retirado:
        raise ValidationError({
            'quantidade': (
                'A quantidade devolvida excede a quantidade ainda retirada para este item do card\u00e1pio.'
            ),
        })

    restante = quantidade
    alocacoes_por_lote = {}
    ordem_lotes = []
    for retirada in reversed(retiradas):
        if restante <= ZERO:
            break
        disponivel = restante_por_lote[retirada.lote_id]
        if disponivel <= ZERO:
            continue
        quantidade_lote = min(_decimal(retirada.quantidade), disponivel, restante)
        if quantidade_lote <= ZERO:
            continue
        if retirada.lote_id not in alocacoes_por_lote:
            alocacoes_por_lote[retirada.lote_id] = ZERO
            ordem_lotes.append(retirada.lote_id)
        alocacoes_por_lote[retirada.lote_id] = (
            alocacoes_por_lote[retirada.lote_id] + quantidade_lote
        ).quantize(Decimal('0.001'))
        restante_por_lote[retirada.lote_id] = (
            disponivel - quantidade_lote
        ).quantize(Decimal('0.001'))
        restante = (restante - quantidade_lote).quantize(Decimal('0.001'))

    if restante > ZERO:
        raise ValidationError({
            'quantidade': (
                'A quantidade devolvida excede a quantidade ainda retirada para este item do card\u00e1pio.'
            ),
        })
    return [
        {'lote_id': lote_id, 'quantidade': alocacoes_por_lote[lote_id]}
        for lote_id in ordem_lotes
    ]


@transaction.atomic
def registrar_devolucao_cardapio(*, item_cardapio, quantidade, usuario, observacao):
    """Devolve ao estoque a sobra entre o liberado e o consumido no preparo."""
    quantidade = _decimal(quantidade)
    if quantidade <= ZERO:
        raise ValidationError({'quantidade': 'A quantidade deve ser maior que zero.'})
    alocacoes_lote = _alocacoes_devolucao_cardapio(
        item_cardapio=item_cardapio,
        quantidade=quantidade,
    )
    return _registrar_movimentacao(
        item_generico_id=item_cardapio.item_generico_id,
        tipo=MovimentacaoEstoque.Tipo.DEVOLUCAO_PREPARO,
        sentido=MovimentacaoEstoque.Sentido.ENTRADA,
        quantidade=quantidade,
        usuario=usuario,
        data_hora=timezone.now(),
        observacao=observacao,
        item_cardapio=item_cardapio,
        alocacoes_lote=alocacoes_lote,
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
    if original.item_cardapio_id:
        raise ValidationError({
            'movimentacao': 'Movimentações de cardápio são corrigidas pelo acerto do consumo real do cardápio.',
        })

    sentido = (
        MovimentacaoEstoque.Sentido.SAIDA
        if original.sentido == MovimentacaoEstoque.Sentido.ENTRADA
        else MovimentacaoEstoque.Sentido.ENTRADA
    )
    alocacoes_estorno = [
        {
            'lote_id': alocacao.lote_id,
            'quantidade': alocacao.quantidade,
        }
        for alocacao in original.alocacoes_lote.all()
    ]
    return _registrar_movimentacao(
        item_generico_id=original.estoque.item_generico_id,
        tipo=MovimentacaoEstoque.Tipo.ESTORNO,
        sentido=sentido,
        quantidade=original.quantidade,
        usuario=usuario,
        data_hora=data_hora or timezone.now(),
        observacao=_justificativa(justificativa),
        movimentacao_estornada=original,
        alocacoes_lote=alocacoes_estorno,
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
    data_recebimento = _data_local(momento)
    valor_deste_recebimento = Decimal('0.00')
    movimentos = []

    for item_ordem in itens_ordem:
        recebido = por_id.get(item_ordem.pk)
        lotes_normalizados = []
        quantidade = ZERO
        if recebido:
            lotes_recebidos = recebido.get('lotes')
            if not lotes_recebidos:
                raise ValidationError({'lotes': 'Informe ao menos um lote para o item recebido.'})

            numeros_lote = set()
            for lote_recebido in lotes_recebidos:
                if not isinstance(lote_recebido, dict):
                    raise ValidationError({'lotes': 'Informe um lote válido para o item recebido.'})

                numero_lote = _numero_lote(lote_recebido.get('numero_lote'))
                if numero_lote.casefold() in numeros_lote:
                    raise ValidationError({
                        'lotes': 'O mesmo lote foi informado mais de uma vez para este item.',
                    })
                data_validade = _data_validade(lote_recebido.get('data_validade'))
                if data_validade < data_recebimento:
                    raise ValidationError({
                        'data_validade': 'A validade do lote não pode ser anterior à data do recebimento.',
                    })
                quantidade_lote = _decimal(lote_recebido.get('quantidade'))
                if quantidade_lote <= ZERO:
                    raise ValidationError({'quantidade': 'A quantidade deve ser maior que zero.'})

                numeros_lote.add(numero_lote.casefold())
                lotes_normalizados.append({
                    'numero_lote': numero_lote,
                    'data_validade': data_validade,
                    'quantidade': quantidade_lote,
                })
                quantidade = (quantidade + quantidade_lote).quantize(Decimal('0.001'))

        solicitada = _decimal(item_ordem.quantidade_solicitada)
        entregue_antes = _decimal(item_ordem.quantidade_entregue)
        pendente_antes = solicitada - entregue_antes
        if quantidade > pendente_antes:
            raise ValidationError({
                'lotes': 'A quantidade total dos lotes não pode exceder a quantidade pendente.',
            })
        if recebido and quantidade < pendente_antes and not str(recebido.get('observacao') or '').strip():
            raise ValidationError({'observacao': 'Informe o motivo da entrega parcial e da quantidade pendente.'})

        item_ordem.quantidade_entregue = entregue_antes + quantidade
        item_ordem.observacao = (recebido or {}).get('observacao') or item_ordem.observacao
        item_ordem.save(update_fields=['quantidade_entregue', 'observacao'])

        if quantidade > ZERO:
            estoque = _estoque_bloqueado(item_ordem.item_empenho.item_ata.item_generico_id)
            alocacoes_lote = []
            for lote_recebido in lotes_normalizados:
                lote = _lote_recebimento_bloqueado(
                    estoque=estoque,
                    numero_lote=lote_recebido['numero_lote'],
                    data_validade=lote_recebido['data_validade'],
                )
                alocacoes_lote.append({
                    'lote_id': lote.pk,
                    'quantidade': lote_recebido['quantidade'],
                })
            movimento = _registrar_movimentacao(
                item_generico_id=item_ordem.item_empenho.item_ata.item_generico_id,
                tipo=MovimentacaoEstoque.Tipo.ENTRADA_FORNECEDOR,
                sentido=MovimentacaoEstoque.Sentido.ENTRADA,
                quantidade=quantidade,
                usuario=usuario,
                data_hora=momento,
                item_ordem=item_ordem,
                alocacoes_lote=alocacoes_lote,
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

