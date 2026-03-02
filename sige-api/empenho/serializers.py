from rest_framework import serializers
from empenho.models import Empenho, ItemEmpenho, OperacaoItem
from licitacao.serializers import AtaSerializer

class EmpenhoSerializer(serializers.ModelSerializer):
    ata = AtaSerializer()
    class Meta:
        model = Empenho
        fields = '__all__'

class ItemEmpenhoSerializer(serializers.ModelSerializer):
    empenho = EmpenhoSerializer()
    class Meta:
        model = ItemEmpenho
        fields = '__all__'

class OperacaoItemSerializer(serializers.ModelSerializer):
    item_empenho = ItemEmpenhoSerializer()
    class Meta:
        model = OperacaoItem
        fields = '__all__'

class ValorEmpenhoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empenho
        fields = ['valor_total']