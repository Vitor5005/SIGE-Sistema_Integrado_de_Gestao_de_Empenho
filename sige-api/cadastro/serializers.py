from rest_framework import serializers
from cadastro.models import Endereco, Fornecedor, ItemGenerico

class EnderecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        fields = ['lagradouro', 'numero', 'bairro', 'cep', 'municipio', 'estado']

class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = ['razao_social', 'nome_fantasia', 'cnpj', 'telefone', 'email', 'endereco']

class ItemGenericoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemGenerico
        fields = ['catmat', 'descricao', 'unidade_medida', 'categoria']

    