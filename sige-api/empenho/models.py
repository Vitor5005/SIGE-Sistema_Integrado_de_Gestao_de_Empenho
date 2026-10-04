from django.conf import settings
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
    quantidade_entrege = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False, verbose_name="Quantidade Entregue do Item no Empenho")
    
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
    data = models.DateTimeField(blank=False, null=False, verbose_name="Data da Operação")
    # Passa a False quando o Diretor registra um reforço, avisando o Técnico até que ele
    # confirme ciência e solicite a entrega ao fornecedor.
    ciente_tecnico = models.BooleanField(default=True)

    def __str__(self):
        return f"Operação: {self.tipo} \n Valor: {self.valor} \n Data: {self.data} \n Item Empenho: {self.item_empenho.id}"


class SolicitacaoReforco(models.Model):
    """
    Pedido do Nutricionista para que o Diretor reforce a quantidade de um
    item do empenho, limitado ao saldo disponível na ARP.
    """

    class Status(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        ATENDIDA = 'ATENDIDA', 'Atendida'
        RECUSADA = 'RECUSADA', 'Recusada'

    item_empenho = models.ForeignKey(ItemEmpenho, on_delete=models.CASCADE, related_name='solicitacoes_reforco')
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    justificativa = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDENTE)
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='solicitacoes_reforco',
    )
    respondida_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacoes_reforco_respondidas',
    )
    resposta = models.TextField(blank=True, default='')
    operacao = models.OneToOneField(
        OperacaoItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacao_reforco',
    )
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_resposta = models.DateTimeField(null=True, blank=True)
    # Passa a False quando o Diretor responde, notificando o solicitante até que ele confirme a leitura.
    vista_pelo_solicitante = models.BooleanField(default=True)

    class Meta:
        ordering = ['-data_solicitacao', '-id']

    def __str__(self):
        return f'Reforço de {self.quantidade} em {self.item_empenho_id} ({self.status})'

# Create your models here.
