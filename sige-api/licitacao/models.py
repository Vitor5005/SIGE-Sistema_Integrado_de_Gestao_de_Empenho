from contextlib import contextmanager

from django.db import connections, models, router, transaction
from cadastro.models import Fornecedor, ItemGenerico


@contextmanager
def _lock_licitacao_atual(using):
    connection = connections[using]
    nome_lock = f"sige:{connection.settings_dict.get('NAME', 'default')}:licitacao-atual"[:64]

    with connection.cursor() as cursor:
        cursor.execute("SELECT GET_LOCK(%s, %s)", [nome_lock, 10])
        adquirido = cursor.fetchone()[0]

    if adquirido != 1:
        raise RuntimeError("Não foi possível obter o lock da licitação atual.")

    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SELECT RELEASE_LOCK(%s)", [nome_lock])


class Licitacao(models.Model):
    numero_licitacao = models.CharField(max_length=50, unique=True, blank=False, null=False, verbose_name="Número da Licitação")
    validade = models.IntegerField(blank=False, null=False, verbose_name="Validade (em meses)")
    data_abertura = models.DateField(blank=False, null=False, verbose_name="Data de Abertura")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição da Licitação")

    atual = models.BooleanField(default=False, db_index=True, verbose_name="Licitação atual")

    def save(self, *args, **kwargs):
        if not self.atual:
            return super().save(*args, **kwargs)

        using = kwargs.get('using') or router.db_for_write(type(self), instance=self)
        with _lock_licitacao_atual(using):
            with transaction.atomic(using=using):
                type(self).objects.using(using).filter(atual=True).exclude(pk=self.pk).update(atual=False)
                return super().save(*args, **kwargs)

    def definir_como_atual(self):
        self.atual = True
        self.save(update_fields=['atual'])

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
