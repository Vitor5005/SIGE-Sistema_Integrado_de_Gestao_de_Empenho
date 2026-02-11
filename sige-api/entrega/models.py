from django.db import models
from empenho.models import Empenho, ItemEmpenho

class OrdemEntrega(models.Model):
    
    empenho = models.ForeignKey(Empenho, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=20, unique=True, null=False, blank=False)
    status_tipo = (
        ("esp", "Em espera"),
        ("con", "Concluída")
    )
    status = models.CharField(max_length=3, choices=status_tipo, default="esp")
    data_emissao = models.DateField(auto_now_add=True)
    data_entrega = models.DateField(null=True, blank=True)
    valor_total_executado = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.codigo

class ItemOrdem(models.Model):
    ordem_entrega = models.ForeignKey(OrdemEntrega, on_delete=models.CASCADE)
    item_empenho = models.ForeignKey(ItemEmpenho, on_delete=models.CASCADE)
    quantidade_solicitada = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_entregue = models.DecimalField(max_digits=10, decimal_places=2)
    observacao = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.ordem_entrega.codigo} - {self.item_empenho.codigo}"

    
# Create your models here.
