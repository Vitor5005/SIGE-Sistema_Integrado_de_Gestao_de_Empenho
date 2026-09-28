from decimal import Decimal

from rest_framework import serializers
from empenho.models import Empenho, ItemEmpenho, OperacaoItem, SolicitacaoReforco
from empenho.services import calcular_saldo_disponivel_item_ata
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


class SolicitacaoReforcoSerializer(serializers.ModelSerializer):
    empenho_id = serializers.IntegerField(source='item_empenho.empenho_id', read_only=True)
    empenho_codigo = serializers.CharField(source='item_empenho.empenho.codigo', read_only=True)
    genero = serializers.CharField(
        source='item_empenho.item_ata.item_generico.descricao',
        read_only=True,
    )
    unidade_medida = serializers.CharField(
        source='item_empenho.item_ata.item_generico.unidade_medida',
        read_only=True,
    )
    solicitante_nome = serializers.CharField(source='solicitante.username', read_only=True)
    ciente_por_nome = serializers.CharField(
        source='ciente_por.username',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = SolicitacaoReforco
        fields = [
            'id',
            'status',
            'item_empenho',
            'quantidade_solicitada',
            'empenho_id',
            'empenho_codigo',
            'genero',
            'unidade_medida',
            'solicitante',
            'solicitante_nome',
            'ciente_por',
            'ciente_por_nome',
            'data_solicitacao',
            'data_ciencia',
        ]
        read_only_fields = [
            'id',
            'status',
            'empenho_id',
            'empenho_codigo',
            'genero',
            'unidade_medida',
            'solicitante',
            'solicitante_nome',
            'ciente_por',
            'ciente_por_nome',
            'data_solicitacao',
            'data_ciencia',
        ]

    def validate_quantidade_solicitada(self, value):
        if value < Decimal('1.00'):
            raise serializers.ValidationError(
                'A quantidade solicitada deve ser de, no mínimo, 1,00.'
            )
        return value

    def validate(self, attrs):
        item_empenho = attrs['item_empenho']
        quantidade_solicitada = attrs['quantidade_solicitada']
        saldo_disponivel = calcular_saldo_disponivel_item_ata(item_empenho.item_ata)

        if quantidade_solicitada > saldo_disponivel:
            raise serializers.ValidationError({
                'quantidade_solicitada': (
                    'A quantidade solicitada excede o saldo disponível na ARP.'
                )
            })

        solicitante = self.context['request'].user
        if SolicitacaoReforco.objects.filter(
            item_empenho=item_empenho,
            solicitante=solicitante,
            status=SolicitacaoReforco.Status.ABERTA,
        ).exists():
            raise serializers.ValidationError({
                'item_empenho': (
                    'Já existe uma solicitação de reforço em aberto para este item.'
                )
            })

        return attrs
    
