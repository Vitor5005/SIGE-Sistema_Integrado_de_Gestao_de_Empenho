from rest_framework import serializers
from empenho.models import Empenho, ItemEmpenho, OperacaoItem

class EmpenhoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empenho
        fields = ['codigo', 'ata', 'valor_total', 'saldo_utilizado']

class ItemEmpenhoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemEmpenho
        fields = ['empenho', 'item_ata', 'quantidade_atual']

class OperacaoItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperacaoItem
        fields = ["item_empenho", "tipo", "valor", "data"]