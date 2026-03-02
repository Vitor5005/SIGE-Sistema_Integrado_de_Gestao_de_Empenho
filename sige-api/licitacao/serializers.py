from rest_framework import serializers
from licitacao.models import Licitacao, Ata, ItemAta
from cadastro.serializers import FornecedorSerializer
from cadastro.serializers import ItemGenericoSerializer
from empenho.models import ItemEmpenho
class LicitacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licitacao
        fields = '__all__'
    
class AtaSerializer(serializers.ModelSerializer):
    licitacao = LicitacaoSerializer()
    fornecedor = FornecedorSerializer()
    class Meta:
        model = Ata
        fields = '__all__'

class ItemAtaSerializer(serializers.ModelSerializer):
    ata = AtaSerializer()
    item_generico = ItemGenericoSerializer()
    class Meta:
        model = ItemAta
        fields = '__all__'
        
class ItensDaAtaSerializer(serializers.ModelSerializer):
    item_generico = ItemGenericoSerializer()
    class Meta:
        model = ItemAta
        fields = '__all__'
        
        
class ItensEmpenhoDaAtaSerializer(serializers.ModelSerializer):
    item_ata = ItensDaAtaSerializer()
    class Meta:
        model = ItemEmpenho
        fields = '__all__'