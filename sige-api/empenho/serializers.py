from rest_framework import serializers
from empenho.models import Empenho, ItemEmpenho, OperacaoItem, SolicitacaoReforco
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


class ReforcoParaPedidoSerializer(serializers.ModelSerializer):
    """Reforço registrado pelo Diretor que o Técnico ainda não confirmou ter visto."""
    empenho_id = serializers.IntegerField(source='item_empenho.empenho_id', read_only=True)
    empenho_codigo = serializers.CharField(source='item_empenho.empenho.codigo', read_only=True)
    fornecedor = serializers.CharField(
        source='item_empenho.empenho.ata.fornecedor.nome_fantasia', read_only=True
    )
    genero = serializers.CharField(source='item_empenho.item_ata.item_generico.descricao', read_only=True)
    unidade_medida = serializers.CharField(
        source='item_empenho.item_ata.item_generico.unidade_medida', read_only=True
    )

    class Meta:
        model = OperacaoItem
        fields = (
            'id', 'valor', 'data', 'ciente_tecnico',
            'empenho_id', 'empenho_codigo', 'fornecedor', 'genero', 'unidade_medida',
        )
        read_only_fields = fields

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
    quantidade_atual_item = serializers.DecimalField(
        source='item_empenho.quantidade_atual',
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    solicitante_nome = serializers.CharField(source='solicitante.username', read_only=True)
    respondida_por_nome = serializers.CharField(
        source='respondida_por.username',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = SolicitacaoReforco
        fields = [
            'id',
            'item_empenho',
            'quantidade',
            'justificativa',
            'status',
            'empenho_id',
            'empenho_codigo',
            'genero',
            'unidade_medida',
            'quantidade_atual_item',
            'solicitante',
            'solicitante_nome',
            'respondida_por',
            'respondida_por_nome',
            'resposta',
            'operacao',
            'data_solicitacao',
            'data_resposta',
            'vista_pelo_solicitante',
        ]
        read_only_fields = [
            'id',
            'status',
            'empenho_id',
            'empenho_codigo',
            'genero',
            'unidade_medida',
            'quantidade_atual_item',
            'solicitante',
            'solicitante_nome',
            'respondida_por',
            'respondida_por_nome',
            'resposta',
            'operacao',
            'data_solicitacao',
            'data_resposta',
            'vista_pelo_solicitante',
        ]
    
