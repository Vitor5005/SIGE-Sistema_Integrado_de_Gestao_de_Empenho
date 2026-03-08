from rest_framework import serializers
from empenho.models import Empenho, ItemEmpenho, OperacaoItem
from licitacao.serializers import AtaSerializer, ItemAtaSerializer

class EmpenhoSerializer(serializers.ModelSerializer):
    ata = AtaSerializer()
    quantidade_itens = serializers.SerializerMethodField()
    
    class Meta:
        model = Empenho
        fields = '__all__'
        
    def get_quantidade_itens(self, instance):
        return ItemEmpenho.objects.filter(empenho=instance).count()
    
class EmpenhoInsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empenho
        fields = '__all__'

class ItemEmpenhoInsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemEmpenho
        fields = '__all__'

class ItemEmpenhoSerializer(serializers.ModelSerializer):
    item_ata = ItemAtaSerializer()
    empenho = EmpenhoSerializer()
    class Meta:
        model = ItemEmpenho
        fields = '__all__'
        
class OperacaoItemInsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperacaoItem
        fields = '__all__'
    
class OperacaoItemSerializer(serializers.ModelSerializer):
    item_empenho = ItemEmpenhoSerializer()
    class Meta:
        model = OperacaoItem
        fields = '__all__'

class ValorEmpenhoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empenho
        fields = ['id', 'codigo','valor_total', 'saldo_utilizado']
    
