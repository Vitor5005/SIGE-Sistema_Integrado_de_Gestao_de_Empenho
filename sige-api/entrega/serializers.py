from rest_framework import serializers
from entrega.models import OrdemEntrega, ItemOrdem
from empenho.serializers import EmpenhoSerializer, ItemEmpenhoSerializer, itemEmpenhoSemEmpenhoSerializer

class OrdemEntregaInsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdemEntrega
        fields = '__all__'

class OrdemEntregaSerializer(serializers.ModelSerializer):
    empenho = EmpenhoSerializer()
    class Meta:
        model = OrdemEntrega
        fields = '__all__'

class itemOrdemInsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemOrdem
        fields = '__all__'

class ItemOrdemSerializer(serializers.ModelSerializer):
    item_empenho = itemEmpenhoSemEmpenhoSerializer()
    quantidade_pendente = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    class Meta:
        model = ItemOrdem
        fields = '__all__'

