from rest_framework import serializers
from entrega.models import OrdemEntrega, ItemOrdem
from empenho.serializers import EmpenhoSerializer, ItemEmpenhoSerializer, itemEmpenhoSemEmpenhoSerializer
class OrdemEntregaSerializer(serializers.ModelSerializer):
    empenho = EmpenhoSerializer()
    class Meta:
        model = OrdemEntrega
        fields = '__all__'

class ItemOrdemSerializer(serializers.ModelSerializer):
    item_empenho = itemEmpenhoSemEmpenhoSerializer()
    class Meta:
        model = ItemOrdem
        fields = '__all__'

