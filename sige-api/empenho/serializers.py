from rest_framework import serializers
from empenho.models import Empenho, ItemEmpenho, OperacaoItem
from licitacao.serializers import AtaSerializer, ItemAtaSerializer, itemAtaSemAtaSerializer

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


class EmpenhoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empenho
        fields = ['codigo']

    def to_internal_value(self, data):
        campos_permitidos = {'codigo'}
        campos_invalidos = sorted(set(data.keys()) - campos_permitidos)
        if campos_invalidos:
            raise serializers.ValidationError({
                campo: 'Este campo não pode ser alterado nesta edição.'
                for campo in campos_invalidos
            })
        return super().to_internal_value(data)

    def validate_codigo(self, value):
        return value.strip().upper()

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
        
class itemEmpenhoSemEmpenhoSerializer(serializers.ModelSerializer):
    item_ata = itemAtaSemAtaSerializer()
    class Meta:
        model = ItemEmpenho
        fields = '__all__'
    
