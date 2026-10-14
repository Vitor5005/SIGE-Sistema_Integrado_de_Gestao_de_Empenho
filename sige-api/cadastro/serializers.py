from rest_framework import serializers
from cadastro.models import Endereco, Fornecedor, ItemGenerico

class EnderecoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endereco
        fields = '__all__'

class FornecedorSerializer(serializers.ModelSerializer):
    endereco = EnderecoSerializer()
    class Meta:
        model = Fornecedor
        fields = '__all__'
        
class FornecedorCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = '__all__'

class ItemGenericoSerializer(serializers.ModelSerializer):
    # A foto é enviada pela ação /imagem/ (multipart); aqui só é exibida como URL.
    imagem = serializers.ImageField(read_only=True)

    class Meta:
        model = ItemGenerico
        fields = '__all__'


class ItemGenericoImagemSerializer(serializers.Serializer):
    TAMANHO_MAXIMO = 2 * 1024 * 1024
    FORMATOS_ACEITOS = {'JPEG', 'PNG', 'WEBP'}

    imagem = serializers.ImageField()

    def validate_imagem(self, imagem):
        if imagem.size > self.TAMANHO_MAXIMO:
            raise serializers.ValidationError('A imagem deve ter no máximo 2 MB.')

        formato = getattr(getattr(imagem, 'image', None), 'format', None)
        if formato not in self.FORMATOS_ACEITOS:
            raise serializers.ValidationError('Envie uma imagem JPG, PNG ou WebP.')

        return imagem

    