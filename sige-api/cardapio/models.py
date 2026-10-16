from django.conf import settings
from django.db import models
from django.db.models import Q

from cadastro.models import ItemGenerico


class Cardapio(models.Model):
    """Cardápio quantitativo de uma refeição, elaborado pela Nutricionista.

    Fluxo: RASCUNHO -> ENVIADO -> APROVADO (retirada do estoque) ->
    CONSUMO_INFORMADO -> FINALIZADO (sobras devolvidas / uso extra retirado).
    O Estoquista pode recusar o envio (RECUSADO) ou devolver o consumo
    informado para correção (volta a APROVADO).

    Alterações de última hora: enquanto ENVIADO, a Nutricionista pode cancelar o envio
    (volta a RASCUNHO). Depois de APROVADO, ela solicita a alteração (ALTERACAO_SOLICITADA);
    se o Estoquista aceitar, o liberado volta ao estoque, este cardápio fica SUBSTITUIDO e
    nasce um rascunho igual para ser ajustado e reenviado. As movimentações do estoque
    continuam presas aos itens do cardápio original.
    """

    class Refeicao(models.TextChoices):
        CAFE = 'CAFE', 'Café da manhã'
        ALMOCO = 'ALMOCO', 'Almoço'
        JANTAR = 'JANTAR', 'Jantar'

    class Status(models.TextChoices):
        RASCUNHO = 'RASCUNHO', 'Rascunho'
        ENVIADO = 'ENVIADO', 'Aguardando aprovação do estoque'
        RECUSADO = 'RECUSADO', 'Recusado pelo estoque'
        APROVADO = 'APROVADO', 'Retirada aprovada'
        CONSUMO_INFORMADO = 'CONSUMO_INFORMADO', 'Consumo aguardando confirmação'
        FINALIZADO = 'FINALIZADO', 'Finalizado'
        ALTERACAO_SOLICITADA = 'ALTERACAO_SOLICITADA', 'Alteração aguardando o estoque'
        SUBSTITUIDO = 'SUBSTITUIDO', 'Substituído por alteração'

    STATUS_EDITAVEIS = (Status.RASCUNHO, Status.RECUSADO)

    refeicao = models.CharField(max_length=10, choices=Refeicao.choices)
    data = models.DateField()
    estimativa_pessoas = models.PositiveIntegerField()
    # Uma preparação por linha (ex.: "ARROZ BRANCO").
    preparacoes = models.TextField()
    observacoes = models.TextField(blank=True, default='')
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.RASCUNHO)
    # Motivo da última recusa do envio ou da devolução do consumo pelo Estoquista.
    motivo_recusa = models.CharField(max_length=500, blank=True, default='')
    # Motivo do pedido de alteração feito pela Nutricionista após a aprovação.
    motivo_alteracao = models.CharField(max_length=500, blank=True, default='')
    # Rascunho criado quando o Estoquista aceita a alteração deste cardápio.
    substituido_por = models.OneToOneField(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='substitui',
    )

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='cardapios_criados',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    enviado_em = models.DateTimeField(null=True, blank=True)
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='+',
    )
    aprovado_em = models.DateTimeField(null=True, blank=True)
    consumo_informado_em = models.DateTimeField(null=True, blank=True)
    finalizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='+',
    )
    finalizado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-data', '-id']
        constraints = [
            models.CheckConstraint(condition=Q(estimativa_pessoas__gt=0), name='cardapio_estimativa_positiva'),
        ]

    def __str__(self):
        return f'{self.get_refeicao_display()} de {self.data:%d/%m/%Y}'

    @property
    def editavel(self):
        return self.status in self.STATUS_EDITAVEIS


class ItemCardapio(models.Model):
    cardapio = models.ForeignKey(Cardapio, on_delete=models.CASCADE, related_name='itens')
    ordem = models.PositiveIntegerField(default=0)
    # Agrupa as linhas do detalhamento (ex.: "SALADA: MAIONESE DE BATATA DOCE"); vazio = preparações principais.
    secao = models.CharField(max_length=150, blank=True, default='')
    item_generico = models.ForeignKey(ItemGenerico, on_delete=models.PROTECT, related_name='itens_cardapio')
    quantidade_planejada = models.DecimalField(max_digits=12, decimal_places=3)
    # Definida pelo Estoquista na aprovação; é o que sai do estoque.
    quantidade_liberada = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    # Informada pela Nutricionista após o preparo.
    quantidade_consumida = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    observacao = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        ordering = ['ordem', 'id']
        constraints = [
            models.CheckConstraint(
                condition=Q(quantidade_planejada__gt=0),
                name='item_cardapio_planejada_positiva',
            ),
            models.CheckConstraint(
                condition=Q(quantidade_liberada__isnull=True) | Q(quantidade_liberada__gte=0),
                name='item_cardapio_liberada_nao_negativa',
            ),
            models.CheckConstraint(
                condition=Q(quantidade_consumida__isnull=True) | Q(quantidade_consumida__gte=0),
                name='item_cardapio_consumida_nao_negativa',
            ),
        ]

    def __str__(self):
        return f'{self.cardapio} - {self.item_generico}'
