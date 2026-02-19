from rest_framework import serializers
from cadastro.models import Endereco, Fornecedor, ItemGenerico

class EnderecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        fields = "__all__"

class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = "__all__"

class ItemGenericoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemGenerico
        fields = "__all__"

    