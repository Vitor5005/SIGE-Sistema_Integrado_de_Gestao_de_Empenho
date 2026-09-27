from django.conf import settings
from django.db import models
from empenho.models import Empenho, ItemEmpenho

class OrdemEntrega(models.Model):
    
    empenho = models.ForeignKey(Empenho, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20, unique=True, null=False, blank=False)
    status_tipo = (
        ("esp", "Em espera"),
        ("par", "Parcialmente entregue"),
        ("con", "Concluída")
    )
    status = models.CharField(max_length=3, choices=status_tipo, default="esp")
    data_emissao = models.DateTimeField(auto_now_add=True)
    data_entrega_prevista = models.DateTimeField()
    data_entrega = models.DateTimeField(null=True, blank=True)
    valor_total_executado = models.DecimalField(max_digits=10, decimal_places=2)
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordens_solicitadas',
    )

    def __str__(self):
        return self.codigo

class ItemOrdem(models.Model):
    ordem_entrega = models.ForeignKey(OrdemEntrega, on_delete=models.CASCADE)
    item_empenho = models.ForeignKey(ItemEmpenho, on_delete=models.CASCADE)
    quantidade_solicitada = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_entregue = models.DecimalField(max_digits=10, decimal_places=2)
    observacao = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.ordem_entrega.codigo} - {self.item_empenho}"

    @property
    def quantidade_pendente(self):
        return max(0, self.quantidade_solicitada - self.quantidade_entregue)


class PendenciaFornecedor(models.Model):
    """
    Quantidade de um item da ordem que o fornecedor ainda deve entregar.
    Gerada no recebimento parcial e resolvida quando o saldo pendente zera.
    """

    class Status(models.TextChoices):
        ABERTA = 'ABERTA', 'Aberta'
        CIENTE = 'CIENTE', 'Ciente'
        RESOLVIDA = 'RESOLVIDA', 'Resolvida'

    item_ordem = models.ForeignKey(ItemOrdem, on_delete=models.CASCADE, related_name='pendencias')
    quantidade_pendente = models.DecimalField(max_digits=12, decimal_places=3)
    motivo = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ABERTA)
    registrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='pendencias_registradas',
    )
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pendencias_recebidas',
    )
    ciente_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pendencias_cientes',
    )
    data_registro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    data_ciencia = models.DateTimeField(null=True, blank=True)
    data_resolucao = models.DateTimeField(null=True, blank=True)

    # Há no máximo uma pendência não resolvida por item; a regra é garantida em
    # entrega.pendencias (MySQL não suporta UniqueConstraint condicional).
    class Meta:
        ordering = ['-data_atualizacao', '-id']

    def __str__(self):
        return f'{self.item_ordem} - {self.quantidade_pendente} ({self.status})'
