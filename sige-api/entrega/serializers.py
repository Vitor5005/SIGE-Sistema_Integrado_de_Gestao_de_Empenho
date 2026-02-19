from rest_framework import serializers
from entrega.models import OrdemEntrega, ItemOrdem

class OrdemEntregaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdemEntrega
        fields = ['empenho', 'codigo', 'status', 'data_emissao', 'data_entrega', 'valor_total_executado']

class ItemOrdemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemOrdem
        fields = ['ordem_entrega', 'item_empenho', 'quantidade_solicitada', 'quantidade_entregue', 'observacao']

