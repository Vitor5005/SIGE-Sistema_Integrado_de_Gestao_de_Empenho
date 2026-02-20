from rest_framework import serializers
from entrega.models import OrdemEntrega, ItemOrdem
from empenho.serializers import EmpenhoSerializer, ItemEmpenhoSerializer
class OrdemEntregaSerializer(serializers.ModelSerializer):
    empenho = EmpenhoSerializer()
    class Meta:
        model = OrdemEntrega
        fields = '__all__'

class ItemOrdemSerializer(serializers.ModelSerializer):
    ordem_entrega = OrdemEntregaSerializer()
    item_empenho = ItemEmpenhoSerializer()
    class Meta:
        model = ItemOrdem
        fields = '__all__'

