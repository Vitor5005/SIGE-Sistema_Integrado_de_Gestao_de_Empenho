from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from cadastro.models import ItemGenerico
from entrega.models import ItemOrdem


class Estoque(models.Model):
    item_generico = models.OneToOneField(
        ItemGenerico,
        on_delete=models.PROTECT,
        related_name='estoque',
    )
    saldo_atual = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['item_generico__descricao', 'id']
        constraints = [
            models.CheckConstraint(
                condition=Q(saldo_atual__gte=0),
                name='estoque_saldo_nao_negativo',
            ),
        ]

    def __str__(self):
        return f'{self.item_generico} - {self.saldo_atual}'


class LoteEstoque(models.Model):
    NUMERO_LOTE_LEGADO = 'LEGADO'

    estoque = models.ForeignKey(
        Estoque,
        on_delete=models.PROTECT,
        related_name='lotes',
    )
    numero_lote = models.CharField(max_length=100)
    data_validade = models.DateField(null=True, blank=True)
    saldo_atual = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    legado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['estoque_id', 'data_validade', 'numero_lote', 'id']
        indexes = [
            models.Index(fields=['estoque', 'data_validade'], name='lote_estoque_val_idx'),
            models.Index(fields=['data_validade', 'saldo_atual'], name='lote_validade_saldo_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['estoque', 'numero_lote'],
                name='lote_unico_por_estoque',
            ),
            models.CheckConstraint(
                condition=Q(saldo_atual__gte=0),
                name='lote_saldo_nao_negativo',
            ),
            models.CheckConstraint(
                condition=~Q(numero_lote=''),
                name='lote_numero_nao_vazio',
            ),
            models.CheckConstraint(
                condition=(
                    Q(legado=True, data_validade__isnull=True)
                    | Q(legado=False, data_validade__isnull=False)
                ),
                name='lote_validade_coerente',
            ),
        ]

    def __str__(self):
        return f'{self.estoque.item_generico} - Lote {self.numero_lote}'


class Inventario(models.Model):
    class Tipo(models.TextChoices):
        CARGA_INICIAL = 'CARGA_INICIAL', 'Carga inicial'
        PERIODICO = 'PERIODICO', 'Periódico'

    class Status(models.TextChoices):
        ABERTO = 'ABERTO', 'Aberto'
        FINALIZADO = 'FINALIZADO', 'Finalizado'

    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABERTO)
    data_contagem = models.DateTimeField()
    data_finalizacao = models.DateTimeField(null=True, blank=True)
    observacao = models.CharField(max_length=500, null=True, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ['-data_contagem', '-id']
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(status='ABERTO', data_finalizacao__isnull=True)
                    | Q(status='FINALIZADO', data_finalizacao__isnull=False)
                ),
                name='inventario_status_finalizacao_coerente',
            ),
        ]


class ItemInventario(models.Model):
    inventario = models.ForeignKey(Inventario, on_delete=models.PROTECT, related_name='itens')
    estoque = models.ForeignKey(Estoque, on_delete=models.PROTECT, related_name='itens_inventario')
    saldo_sistema = models.DecimalField(max_digits=12, decimal_places=3)
    quantidade_contada = models.DecimalField(max_digits=12, decimal_places=3)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['inventario', 'estoque'],
                name='item_inventario_unico_por_estoque',
            ),
            models.CheckConstraint(
                condition=Q(saldo_sistema__gte=0) & Q(quantidade_contada__gte=0),
                name='item_inventario_quantidades_nao_negativas',
            ),
        ]


class MovimentacaoEstoqueQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Movimentações de estoque são imutáveis; use estorno.')

    def delete(self):
        raise ValidationError('Movimentações de estoque não podem ser excluídas; use estorno.')


class MovimentacaoEstoque(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA_FORNECEDOR = 'ENTRADA_FORNECEDOR', 'Entrada de fornecedor'
        CARGA_INICIAL = 'CARGA_INICIAL', 'Carga inicial'
        AJUSTE_POSITIVO = 'AJUSTE_POSITIVO', 'Inventário (sobra)'
        AJUSTE_NEGATIVO = 'AJUSTE_NEGATIVO', 'Inventário (falta)'
        SAIDA_PRODUCAO = 'SAIDA_PRODUCAO', 'Consumo no preparo de refeições'
        DEVOLUCAO_PREPARO = 'DEVOLUCAO_PREPARO', 'Devolução de sobras do preparo'
        SAIDA_DOACAO = 'SAIDA_DOACAO', 'Doação'
        SAIDA_PERDA = 'SAIDA_PERDA', 'Perda ou vencimento'
        ESTORNO = 'ESTORNO', 'Estorno'

    class Sentido(models.TextChoices):
        ENTRADA = 'E', 'Entrada'
        SAIDA = 'S', 'Saída'

    estoque = models.ForeignKey(Estoque, on_delete=models.PROTECT, related_name='movimentacoes')
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    sentido = models.CharField(max_length=1, choices=Sentido.choices)
    quantidade = models.DecimalField(max_digits=12, decimal_places=3)
    saldo_resultante = models.DecimalField(max_digits=12, decimal_places=3)
    data_hora = models.DateTimeField()
    data_registro = models.DateTimeField(auto_now_add=True)
    observacao = models.CharField(max_length=255, null=True, blank=True)
    item_ordem = models.ForeignKey(
        ItemOrdem,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='movimentacoes_estoque',
    )
    item_inventario = models.OneToOneField(
        ItemInventario,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='movimentacao_estoque',
    )
    # Saídas e devoluções geradas por um cardápio (retirada aprovada e acerto do consumo real).
    item_cardapio = models.ForeignKey(
        'cardapio.ItemCardapio',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='movimentacoes_estoque',
    )
    movimentacao_estornada = models.OneToOneField(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='estorno',
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    papel = models.CharField(max_length=5)

    objects = MovimentacaoEstoqueQuerySet.as_manager()

    class Meta:
        ordering = ['-data_hora', '-id']
        indexes = [
            models.Index(fields=['estoque', 'data_hora'], name='mov_estoque_data_idx'),
            models.Index(fields=['tipo', 'data_hora'], name='mov_tipo_data_idx'),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(quantidade__gt=0), name='mov_quantidade_positiva'),
            models.CheckConstraint(condition=Q(saldo_resultante__gte=0), name='mov_saldo_nao_negativo'),
            models.CheckConstraint(
                condition=(
                    Q(tipo__in=['ENTRADA_FORNECEDOR', 'CARGA_INICIAL', 'AJUSTE_POSITIVO', 'DEVOLUCAO_PREPARO'], sentido='E')
                    | Q(tipo__in=['AJUSTE_NEGATIVO', 'SAIDA_PRODUCAO', 'SAIDA_DOACAO', 'SAIDA_PERDA'], sentido='S')
                    | Q(tipo='ESTORNO')
                ),
                name='mov_sentido_por_tipo',
            ),
            models.CheckConstraint(
                condition=(
                    Q(tipo='ENTRADA_FORNECEDOR', item_ordem__isnull=False)
                    | (~Q(tipo='ENTRADA_FORNECEDOR') & Q(item_ordem__isnull=True))
                ),
                name='mov_entrada_exige_item_ordem',
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        tipo__in=['CARGA_INICIAL', 'AJUSTE_POSITIVO', 'AJUSTE_NEGATIVO'],
                        item_inventario__isnull=False,
                    )
                    | (
                        ~Q(tipo__in=['CARGA_INICIAL', 'AJUSTE_POSITIVO', 'AJUSTE_NEGATIVO'])
                        & Q(item_inventario__isnull=True)
                    )
                ),
                name='mov_ajuste_exige_item_inventario',
            ),
            models.CheckConstraint(
                condition=(
                    Q(tipo='ESTORNO', movimentacao_estornada__isnull=False)
                    | (~Q(tipo='ESTORNO') & Q(movimentacao_estornada__isnull=True))
                ),
                name='mov_estorno_exige_origem',
            ),
            models.CheckConstraint(
                condition=(
                    Q(tipo='DEVOLUCAO_PREPARO', item_cardapio__isnull=False)
                    | ~Q(tipo='DEVOLUCAO_PREPARO')
                ),
                name='mov_devolucao_exige_item_cardapio',
            ),
            models.CheckConstraint(
                condition=(
                    Q(tipo='ENTRADA_FORNECEDOR')
                    | (Q(observacao__isnull=False) & ~Q(observacao=''))
                ),
                name='mov_observacao_obrigatoria',
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Movimentações de estoque são imutáveis; use estorno.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Movimentações de estoque não podem ser excluídas; use estorno.')

class MovimentacaoLoteQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Movimentações por lote são imutáveis; use estorno.')

    def delete(self):
        raise ValidationError('Movimentações por lote não podem ser excluídas; use estorno.')


class MovimentacaoLote(models.Model):
    movimentacao = models.ForeignKey(
        MovimentacaoEstoque,
        on_delete=models.PROTECT,
        related_name='alocacoes_lote',
    )
    lote = models.ForeignKey(
        LoteEstoque,
        on_delete=models.PROTECT,
        related_name='movimentacoes',
    )
    quantidade = models.DecimalField(max_digits=12, decimal_places=3)
    saldo_lote_resultante = models.DecimalField(max_digits=12, decimal_places=3)

    objects = MovimentacaoLoteQuerySet.as_manager()

    class Meta:
        ordering = ['movimentacao_id', 'id']
        constraints = [
            models.CheckConstraint(
                condition=Q(quantidade__gt=0),
                name='mov_lote_quantidade_positiva',
            ),
            models.CheckConstraint(
                condition=Q(saldo_lote_resultante__gte=0),
                name='mov_lote_saldo_nao_negativo',
            ),
            models.UniqueConstraint(
                fields=['movimentacao', 'lote'],
                name='mov_lote_unico',
            ),
        ]

    def clean(self):
        super().clean()
        if (
            self.movimentacao_id
            and self.lote_id
            and self.movimentacao.estoque_id != self.lote.estoque_id
        ):
            raise ValidationError({
                'lote': (
                    'O lote informado não pertence ao mesmo estoque '
                    'da movimentação.'
                )
            })

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError('Movimentações por lote são imutáveis; use estorno.')
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Movimentações por lote não podem ser excluídas; use estorno.')
