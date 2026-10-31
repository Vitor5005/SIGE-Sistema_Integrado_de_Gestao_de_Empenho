from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from cardapio.models import Cardapio, ItemCardapio
from estoque.models import Estoque
from utils.estoque_services import (
    STATUS_VALIDADE_DESCRICOES,
    dias_para_data_validade,
    lotes_utilizaveis_queryset,
    registrar_devolucao_cardapio,
    registrar_saida_cardapio,
    saldos_utilizaveis_por_estoque,
    status_data_validade,
)

ZERO = Decimal('0.000')
TRES_CASAS = Decimal('0.001')

# O servidor trabalha em UTC; "hoje" é o dia no Acre, onde fica o Restaurante Universitário.
FUSO_RU = ZoneInfo('America/Rio_Branco')


def hoje_no_ru():
    return datetime.now(FUSO_RU).date()


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
            'itens': [
                f'{item.item_generico.descricao}: quantidade disponível para uso insuficiente para retirar '
                f'{quantidade.normalize():f} {item.item_generico.unidade_medida}.',
            ],
        })


def _bloquear(cardapio_id, status_permitidos, mensagem):
    cardapio = Cardapio.objects.select_for_update().get(pk=cardapio_id)
    if cardapio.status not in status_permitidos:
        raise ValidationError({'status': mensagem})
    return cardapio


def _bloquear_estoques_dos_itens(itens):
    item_generico_ids = sorted({item.item_generico_id for item in itens})
    if not item_generico_ids:
        return []
    return list(
        Estoque.objects.select_for_update()
        .filter(item_generico_id__in=item_generico_ids)
        .order_by('item_generico_id')
    )


def quantidades_reservadas(excluir_cardapio_id=None):
    """Soma, por gênero, o planejado em cardápios enviados que ainda aguardam aprovação."""
    itens = ItemCardapio.objects.filter(cardapio__status=Cardapio.Status.ENVIADO)
    if excluir_cardapio_id:
        itens = itens.exclude(cardapio_id=excluir_cardapio_id)
    return {
        linha['item_generico_id']: linha['total']
        for linha in itens.values('item_generico_id').annotate(total=Sum('quantidade_planejada'))
    }


def _prioridades_validade_por_estoque(estoques, reservado_por_genero, data_referencia):
    """Simula as reservas em FEFO para informar lotes próximos do vencimento.

    A simulação é somente leitura: a retirada real continua sendo feita no fluxo de
    aprovação do cardápio. Todos os lotes utilizáveis são carregados em uma consulta.
    """
    prioridades = {
        estoque.id: {
            'quantidade_prioritaria': ZERO,
            'lotes_prioritarios': [],
            'proxima_validade': None,
            'dias_para_proxima_validade': None,
            'status_proxima_validade': None,
            'status_proxima_validade_descricao': None,
        }
        for estoque in estoques
    }
    if not prioridades:
        return prioridades

    reserva_restante_por_estoque = {
        estoque.id: reservado_por_genero.get(estoque.item_generico_id, ZERO)
        for estoque in estoques
    }
    lotes = (
        lotes_utilizaveis_queryset(data_referencia)
        .filter(estoque_id__in=list(prioridades))
        .order_by('estoque_id', 'legado', 'data_validade', 'id')
    )

    for lote in lotes:
        dados_estoque = prioridades[lote.estoque_id]
        reserva_restante = reserva_restante_por_estoque[lote.estoque_id]
        quantidade_disponivel = lote.saldo_atual
        if reserva_restante > ZERO:
            consumido_pela_reserva = min(reserva_restante, quantidade_disponivel)
            reserva_restante_por_estoque[lote.estoque_id] = reserva_restante - consumido_pela_reserva
            quantidade_disponivel -= consumido_pela_reserva

        if quantidade_disponivel <= ZERO or lote.legado:
            continue

        dias_para_validade = dias_para_data_validade(lote.data_validade, data_referencia)
        status_validade = status_data_validade(lote.data_validade, data_referencia)
        if dados_estoque['proxima_validade'] is None:
            dados_estoque.update({
                'proxima_validade': lote.data_validade.isoformat(),
                'dias_para_proxima_validade': dias_para_validade,
                'status_proxima_validade': status_validade,
                'status_proxima_validade_descricao': STATUS_VALIDADE_DESCRICOES[status_validade],
            })

        if status_validade not in {'VENCE_HOJE', 'CRITICO', 'ATENCAO'}:
            continue

        dados_estoque['quantidade_prioritaria'] += quantidade_disponivel
        dados_estoque['lotes_prioritarios'].append({
            'id': lote.id,
            'numero_lote': lote.numero_lote,
            'data_validade': lote.data_validade.isoformat(),
            'dias_para_validade': dias_para_validade,
            'status': status_validade,
            'status_descricao': STATUS_VALIDADE_DESCRICOES[status_validade],
            'quantidade_disponivel': quantidade_disponivel,
        })
    return prioridades


def disponibilidade(excluir_cardapio_id=None, data_referencia=None):
    """Saldo físico, utilizável, reservado e disponível de cada gênero com estoque."""
    data_referencia = data_referencia or hoje_no_ru()
    reservado = quantidades_reservadas(excluir_cardapio_id)
    estoques = list(Estoque.objects.select_related('item_generico').order_by('item_generico__descricao'))
    saldos_utilizaveis = saldos_utilizaveis_por_estoque(
        [estoque.id for estoque in estoques], data_referencia,
    )
    prioridades_por_estoque = _prioridades_validade_por_estoque(
        estoques,
        reservado,
        data_referencia,
    )
    dados = []
    for estoque in estoques:
        genero = estoque.item_generico
        reservado_item = reservado.get(genero.id, ZERO)
        saldo_utilizavel = saldos_utilizaveis.get(estoque.id, ZERO)
        prioridades = prioridades_por_estoque[estoque.id]
        dados.append({
            'item_generico_id': genero.id,
            'catmat': genero.catmat,
            'descricao': genero.descricao,
            'unidade_medida': genero.unidade_medida,
            'categoria': genero.categoria,
            'categoria_descricao': genero.get_categoria_display(),
            'imagem': genero.imagem.url if genero.imagem else None,
            'conteudo_embalagem': genero.conteudo_embalagem,
            'unidade_embalagem': genero.unidade_embalagem,
            'saldo_atual': estoque.saldo_atual,
            'saldo_utilizavel': saldo_utilizavel,
            'reservado': reservado_item,
            'disponivel': max(saldo_utilizavel - reservado_item, ZERO),
            **prioridades,
        })
    return dados


def faltas_de_saldo(
    planejado,
    generos,
    excluir_cardapio_id=None,
    bloquear=False,
    data_referencia=None,
):
    """Mensagens dos gêneros sem saldo ou com quantidade acima do disponível.

    `planejado` soma por gênero o que o cardápio pretende usar; `generos` mapeia o id para o
    ItemGenerico (para as mensagens). Com `bloquear`, trava os saldos até o fim da transação.
    """
    estoques = Estoque.objects.filter(item_generico_id__in=planejado).order_by('item_generico_id')
    if bloquear:
        estoques = estoques.select_for_update()
    estoques = list(estoques)
    saldos_por_estoque = saldos_utilizaveis_por_estoque(
        [estoque.id for estoque in estoques], data_referencia,
    )
    saldos = {
        estoque.item_generico_id: saldos_por_estoque.get(estoque.id, ZERO)
        for estoque in estoques
    }
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
    faltas = faltas_de_saldo(
        planejado,
        generos,
        excluir_cardapio_id=cardapio.pk,
        bloquear=True,
        data_referencia=cardapio.data,
    )
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
def cancelar_envio(*, cardapio_id, usuario):
    """A Nutricionista retira o cardápio da fila do estoque para alterá-lo; nada saiu do estoque ainda."""
    cardapio = _bloquear(
        cardapio_id, [Cardapio.Status.ENVIADO], 'Somente cardápios aguardando o estoque podem ter o envio cancelado.',
    )
    cardapio.status = Cardapio.Status.RASCUNHO
    cardapio.enviado_em = None
    cardapio.save(update_fields=['status', 'enviado_em', 'atualizado_em'])
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
    nunca maior, e nunca acima do saldo utilizável.
    """
    cardapio = _bloquear(cardapio_id, [Cardapio.Status.ENVIADO], 'Somente cardápios enviados podem ser aprovados.')
    itens = list(cardapio.itens.select_related('item_generico'))
    _bloquear_estoques_dos_itens(itens)
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
    # Um pedido de alteração recusado deixa de importar depois que o consumo é informado.
    cardapio.motivo_alteracao = ''
    cardapio.save(update_fields=[
        'status', 'consumo_informado_em', 'motivo_recusa', 'motivo_alteracao', 'atualizado_em',
    ])
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
    Consumiu mais: o excedente é retirado (SAIDA_PRODUCAO), limitado ao saldo utilizável.
    """
    cardapio = _bloquear(
        cardapio_id, [Cardapio.Status.CONSUMO_INFORMADO], 'Não há consumo aguardando confirmação.',
    )
    referencia = _referencia(cardapio)
    itens = list(cardapio.itens.select_related('item_generico'))
    _bloquear_estoques_dos_itens(itens)
    for item in itens:
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


@transaction.atomic
def solicitar_alteracao(*, cardapio_id, motivo, usuario):
    """A Nutricionista pede para alterar um cardápio cuja retirada já foi aprovada."""
    cardapio = _bloquear(
        cardapio_id, [Cardapio.Status.APROVADO],
        'A alteração só pode ser solicitada após a aprovação e antes de informar o consumo.',
    )
    if cardapio.data < hoje_no_ru():
        raise ValidationError({'status': 'Não é possível alterar o cardápio de um dia que já passou.'})
    motivo = (motivo or '').strip()
    if not motivo:
        raise ValidationError({'motivo': 'Informe o motivo da alteração.'})

    cardapio.status = Cardapio.Status.ALTERACAO_SOLICITADA
    cardapio.motivo_alteracao = motivo
    cardapio.motivo_recusa = ''
    cardapio.save(update_fields=['status', 'motivo_alteracao', 'motivo_recusa', 'atualizado_em'])
    return cardapio


@transaction.atomic
def recusar_alteracao(*, cardapio_id, motivo, usuario):
    """O Estoquista não aceita a alteração (ex.: os gêneros já foram para o preparo)."""
    cardapio = _bloquear(
        cardapio_id, [Cardapio.Status.ALTERACAO_SOLICITADA], 'Não há pedido de alteração aguardando o estoque.',
    )
    motivo = (motivo or '').strip()
    if not motivo:
        raise ValidationError({'motivo': 'Informe o motivo da recusa.'})

    cardapio.status = Cardapio.Status.APROVADO
    cardapio.motivo_recusa = motivo
    cardapio.save(update_fields=['status', 'motivo_recusa', 'atualizado_em'])
    return cardapio


@transaction.atomic
def aceitar_alteracao(*, cardapio_id, usuario):
    """Devolve ao estoque tudo o que foi liberado e cria um rascunho igual para a Nutricionista ajustar.

    O cardápio original fica SUBSTITUIDO e mantém suas movimentações; o novo rascunho
    passa de novo por envio e aprovação. Retorna o novo rascunho.
    """
    cardapio = _bloquear(
        cardapio_id, [Cardapio.Status.ALTERACAO_SOLICITADA], 'Não há pedido de alteração aguardando o estoque.',
    )
    itens = list(cardapio.itens.select_related('item_generico'))
    _bloquear_estoques_dos_itens(itens)
    referencia = _referencia(cardapio)
    for item in itens:
        if item.quantidade_liberada and item.quantidade_liberada > ZERO:
            registrar_devolucao_cardapio(
                item_cardapio=item,
                quantidade=item.quantidade_liberada,
                usuario=usuario,
                observacao=f'Devolução por alteração do {referencia}.',
            )

    novo = Cardapio.objects.create(
        refeicao=cardapio.refeicao,
        data=cardapio.data,
        estimativa_pessoas=cardapio.estimativa_pessoas,
        preparacoes=cardapio.preparacoes,
        observacoes=cardapio.observacoes,
        criado_por=cardapio.criado_por,
    )
    ItemCardapio.objects.bulk_create([
        ItemCardapio(
            cardapio=novo,
            ordem=item.ordem,
            secao=item.secao,
            item_generico=item.item_generico,
            quantidade_planejada=item.quantidade_planejada,
            observacao=item.observacao,
        )
        for item in itens
    ])

    cardapio.status = Cardapio.Status.SUBSTITUIDO
    cardapio.substituido_por = novo
    cardapio.motivo_recusa = ''
    cardapio.finalizado_por = usuario
    cardapio.finalizado_em = timezone.now()
    cardapio.save(update_fields=[
        'status', 'substituido_por', 'motivo_recusa', 'finalizado_por', 'finalizado_em', 'atualizado_em',
    ])
    return novo
