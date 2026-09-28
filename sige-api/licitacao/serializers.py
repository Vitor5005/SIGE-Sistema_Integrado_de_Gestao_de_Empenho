from rest_framework import serializers
from django.utils import timezone
from licitacao.models import Licitacao, Ata, ItemAta
from cadastro.serializers import FornecedorSerializer
from cadastro.serializers import ItemGenericoSerializer
from empenho.models import ItemEmpenho
class LicitacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licitacao
        fields = '__all__'


class LicitacaoUpdateSerializer(serializers.ModelSerializer):
    validade = serializers.IntegerField(min_value=1, max_value=120)
    descricao = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Licitacao
        fields = ['numero_licitacao', 'validade', 'data_abertura', 'descricao']

    def to_internal_value(self, data):
        campos_permitidos = {'numero_licitacao', 'validade', 'data_abertura', 'descricao'}
        campos_invalidos = sorted(set(data.keys()) - campos_permitidos)
        if campos_invalidos:
            raise serializers.ValidationError({
                campo: 'Este campo não pode ser alterado nesta edição.'
                for campo in campos_invalidos
            })
        return super().to_internal_value(data)

    def validate_numero_licitacao(self, value):
        return value.strip().upper()

    def validate_data_abertura(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError(
                'A data de abertura não pode estar no futuro.'
            )
        return value

    def validate_descricao(self, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return None
    
class AtaSerializer(serializers.ModelSerializer):
    licitacao = LicitacaoSerializer()
    fornecedor = FornecedorSerializer()
    class Meta:
        model = Ata
        fields = '__all__'


class AtaUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ata
        fields = ['numero_ata']

    def to_internal_value(self, data):
        campos_permitidos = {'numero_ata'}
        campos_invalidos = sorted(set(data.keys()) - campos_permitidos)
        if campos_invalidos:
            raise serializers.ValidationError({
                campo: 'Este campo não pode ser alterado nesta edição.'
                for campo in campos_invalidos
            })
        return super().to_internal_value(data)

    def validate_numero_ata(self, value):
        return value.strip().upper()

class AtaInsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ata
        fields = '__all__'
        
class ItemAtaInsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemAta
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
        
class itemAtaSemAtaSerializer(serializers.ModelSerializer):
    item_generico = ItemGenericoSerializer()
    class Meta:
        model = ItemAta
        fields = '__all__'
