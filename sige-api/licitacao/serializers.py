from rest_framework import serializers
from licitacao.models import Licitacao, Ata, ItemAta

class LicitacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licitacao
        fields = ['numero_licitacao', 'validade', 'data_abertura']
    
class AtaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ata
        fields = ['numero_ata', 'ata_saldo_total', 'licitacao', 'fornecedor']

class ItemAtaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemAta
        fields = ['ata', 'item_generico', 'marca', 'quantidade_licitada', 'valor_unitario']