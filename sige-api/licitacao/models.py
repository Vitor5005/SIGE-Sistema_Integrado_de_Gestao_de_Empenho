from django.db import models
from cadastro.models import Fornecedor, ItemGenerico

class Licitacao(models.Model):
    numero_licitacao = models.CharField(max_length=50, unique=True, blank=False, null=False, verbose_name="Número da Licitação")
    validade = models.IntegerField(blank=False, null=False, verbose_name="Validade (em meses)")
    data_abertura = models.DateField(blank=False, null=False, verbose_name="Data de Abertura")

    def __str__(self):
        return f"Licitacao {self.numero_licitacao} \n Validade: {self.validade} meses \n Data de Abertura: {self.data_abertura}"


class Ata(models.Model):
    numero_ata = models.CharField(max_length=50, unique=True, blank=False, null=False, verbose_name="Número da Ata")
    ata_saldo_total = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False, verbose_name="Saldo Total da Ata")
    licitacao = models.ForeignKey(Licitacao, on_delete=models.CASCADE)
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('licitacao', 'fornecedor')
    
    def __str__(self):
        return f"Ata {self.numero_ata} \n Saldo Total: {self.ata_saldo_total} \n Licitação: {self.licitacao.numero_licitacao} \n Fornecedor: {self.fornecedor.razao_social}"

class ItemAta(models.Model):
    ata = models.ForeignKey(Ata, on_delete=models.CASCADE)
    item_generico = models.ForeignKey(ItemGenerico, on_delete=models.CASCADE)
    marca = models.CharField(max_length=255, blank=False, null=False, verbose_name="Marca do Item")
    quantidade_licitada = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False, verbose_name="Quantidade Licitada")
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False, verbose_name="Valor Unitário")
    
    def __str__(self):
        return f"item: {self.item_generico.descricao} \n Marca: {self.marca} \n Quantidade Licitada: {self.quantidade_licitada} \n Valor Unitário: {self.valor_unitario} \n Ata: {self.ata.numero_ata}"

# Create your models here.
