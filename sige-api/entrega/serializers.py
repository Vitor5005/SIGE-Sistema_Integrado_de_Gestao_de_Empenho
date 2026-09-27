from rest_framework import serializers
from entrega.models import OrdemEntrega, ItemOrdem, PendenciaFornecedor
from empenho.serializers import EmpenhoSerializer, ItemEmpenhoSerializer, itemEmpenhoSemEmpenhoSerializer

class OrdemEntregaInsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdemEntrega
        fields = '__all__'
        read_only_fields = ('solicitante',)

class OrdemEntregaSerializer(serializers.ModelSerializer):
    empenho = EmpenhoSerializer()
    class Meta:
        model = OrdemEntrega
        fields = '__all__'

class itemOrdemInsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemOrdem
        fields = '__all__'

class ItemOrdemSerializer(serializers.ModelSerializer):
    item_empenho = itemEmpenhoSemEmpenhoSerializer()
    quantidade_pendente = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    class Meta:
        model = ItemOrdem
        fields = '__all__'

class PendenciaFornecedorSerializer(serializers.ModelSerializer):
    ordem_id = serializers.IntegerField(source='item_ordem.ordem_entrega_id', read_only=True)
    ordem_codigo = serializers.CharField(source='item_ordem.ordem_entrega.codigo', read_only=True)
    empenho_codigo = serializers.CharField(source='item_ordem.ordem_entrega.empenho.codigo', read_only=True)
    fornecedor = serializers.CharField(
        source='item_ordem.ordem_entrega.empenho.ata.fornecedor.nome_fantasia', read_only=True
    )
    genero = serializers.CharField(
        source='item_ordem.item_empenho.item_ata.item_generico.descricao', read_only=True
    )
    unidade_medida = serializers.CharField(
        source='item_ordem.item_empenho.item_ata.item_generico.unidade_medida', read_only=True
    )
    quantidade_solicitada = serializers.DecimalField(
        source='item_ordem.quantidade_solicitada', max_digits=10, decimal_places=2, read_only=True
    )
    quantidade_entregue = serializers.DecimalField(
        source='item_ordem.quantidade_entregue', max_digits=10, decimal_places=2, read_only=True
    )
    registrada_por_nome = serializers.CharField(source='registrada_por.username', read_only=True)
    destinatario_nome = serializers.CharField(source='destinatario.username', read_only=True, default=None)
    ciente_por_nome = serializers.CharField(source='ciente_por.username', read_only=True, default=None)

    class Meta:
        model = PendenciaFornecedor
        fields = (
            'id', 'status', 'quantidade_pendente', 'motivo',
            'ordem_id', 'ordem_codigo', 'empenho_codigo', 'fornecedor',
            'genero', 'unidade_medida', 'quantidade_solicitada', 'quantidade_entregue',
            'registrada_por', 'registrada_por_nome', 'destinatario', 'destinatario_nome',
            'ciente_por', 'ciente_por_nome',
            'data_registro', 'data_atualizacao', 'data_ciencia', 'data_resolucao',
        )
        read_only_fields = fields

