from django.db import models
from licitacao.models import Ata, ItemAta

class Empenho(models.Model):
    
    codigo = models.CharField(max_length=50, unique=True, blank=False, null=False, verbose_name="Codigo do Empenho")
    ata = models.ForeignKey(Ata, on_delete=models.CASCADE)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False, verbose_name="Valor Total do Empenho")
    saldo_utilizado = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False, verbose_name="Saldo Utilizado do Empenho")
    
    def __str__(self):
        return f"Empenho {self.codigo} \n Valor Total: {self.valor_total} \n Saldo Utilizado: {self.saldo_utilizado} \n Ata: {self.ata.numero_ata}"
    
class ItemEmpenho(models.Model):
    
    empenho = models.ForeignKey(Empenho, on_delete=models.CASCADE)
    item_ata = models.ForeignKey(ItemAta, on_delete=models.CASCADE)
    quantidade_atual = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False, verbose_name="Quantidade Atual do Item no Empenho")
    
    def __str__(self):
        return f"Empenho: {self.empenho.codigo} \n Item Ata: {self.item_ata.item_generico.descricao} \n Quantidade Atual: {self.quantidade_atual}" 
    
class OperacaoItem(models.Model):
    
    item_empenho = models.ForeignKey(ItemEmpenho, on_delete=models.CASCADE)
    operacoes = (
        ("inc", "Inclusão (Inc)"),
        ("ref", "Reforço (Ref)"),
        ("anl", "Anulação (Anl)")
    )    
    tipo = models.CharField(max_length=3, choices=operacoes, blank=False, null=False, verbose_name="Tipo de Operação") 
    valor = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False, verbose_name="Valor da Operação")
    data = models.DateField(blank=False, null=False, verbose_name="Data da Operação")

    def __str__(self):
        return f"Operação: {self.tipo} \n Valor: {self.valor} \n Data: {self.data} \n Item Empenho: {self.item_empenho.id}"

# Create your models here.
