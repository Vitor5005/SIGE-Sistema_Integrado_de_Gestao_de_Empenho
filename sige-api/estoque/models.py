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
        AJUSTE_POSITIVO = 'AJUSTE_POSITIVO', 'Ajuste positivo'
        AJUSTE_NEGATIVO = 'AJUSTE_NEGATIVO', 'Ajuste negativo'
        SAIDA_PRODUCAO = 'SAIDA_PRODUCAO', 'Saída para produção'
        SAIDA_DOACAO = 'SAIDA_DOACAO', 'Saída para doação'
        SAIDA_PERDA = 'SAIDA_PERDA', 'Saída por perda'
        ESTORNO = 'ESTORNO', 'Estorno'

    class Sentido(models.TextChoices):
        ENTRADA = 'E', 'Entrada'
        SAIDA = 'S', 'Saída'

    # TODO: adicionar lote e data de validade somente após definição do domínio.
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
                    Q(tipo__in=['ENTRADA_FORNECEDOR', 'CARGA_INICIAL', 'AJUSTE_POSITIVO'], sentido='E')
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

