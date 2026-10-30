from decimal import Decimal

from rest_framework import serializers

from estoque.models import Estoque, LoteEstoque, MovimentacaoEstoque
from utils.estoque_services import lote_vencido, saldo_utilizavel_estoque


class EstoqueSerializer(serializers.ModelSerializer):
    item_generico_id = serializers.IntegerField(source='item_generico.id', read_only=True)
    catmat = serializers.CharField(source='item_generico.catmat', read_only=True)
    descricao = serializers.CharField(source='item_generico.descricao', read_only=True)
    unidade_medida = serializers.CharField(source='item_generico.unidade_medida', read_only=True)
    categoria = serializers.CharField(source='item_generico.categoria', read_only=True)
    categoria_descricao = serializers.CharField(source='item_generico.get_categoria_display', read_only=True)
    conteudo_embalagem = serializers.DecimalField(
        source='item_generico.conteudo_embalagem', max_digits=10, decimal_places=3, read_only=True
    )
    unidade_embalagem = serializers.CharField(source='item_generico.unidade_embalagem', read_only=True)
    imagem = serializers.ImageField(source='item_generico.imagem', read_only=True)
    possui_carga_inicial = serializers.BooleanField(read_only=True, default=False)
    saldo_utilizavel = serializers.SerializerMethodField()

    def get_saldo_utilizavel(self, estoque):
        return saldo_utilizavel_estoque(estoque)

    class Meta:
        model = Estoque
        fields = (
            'id', 'item_generico_id', 'catmat', 'descricao', 'unidade_medida',
            'categoria', 'categoria_descricao', 'conteudo_embalagem',
            'unidade_embalagem', 'imagem', 'saldo_atual', 'saldo_utilizavel', 'data_atualizacao',
            'possui_carga_inicial',
        )


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    item_generico_id = serializers.IntegerField(source='estoque.item_generico_id', read_only=True)
    genero = serializers.CharField(source='estoque.item_generico.descricao', read_only=True)
    usuario_nome = serializers.CharField(source='usuario.username', read_only=True)
    tipo_descricao = serializers.CharField(source='get_tipo_display', read_only=True)
    ordem_codigo = serializers.CharField(source='item_ordem.ordem_entrega.codigo', read_only=True, allow_null=True)
    cardapio_id = serializers.IntegerField(source='item_cardapio.cardapio_id', read_only=True, allow_null=True)

    class Meta:
        model = MovimentacaoEstoque
        fields = (
            'id', 'item_generico_id', 'genero', 'tipo', 'tipo_descricao', 'sentido', 'quantidade',
            'saldo_resultante', 'data_hora', 'data_registro', 'observacao',
            'item_ordem', 'ordem_codigo', 'item_inventario', 'movimentacao_estornada', 'cardapio_id',
            'usuario', 'usuario_nome', 'papel',
        )
        read_only_fields = fields


class LoteSaidaSerializer(serializers.ModelSerializer):
    vencido = serializers.SerializerMethodField()

    class Meta:
        model = LoteEstoque
        fields = ('id', 'numero_lote', 'data_validade', 'saldo_atual', 'legado', 'vencido')
        read_only_fields = fields

    def get_vencido(self, lote):
        return lote_vencido(lote)


class SaidaSerializer(serializers.Serializer):
    item_generico_id = serializers.IntegerField(min_value=1)
    quantidade = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal('0.001'))
    tipo_saida = serializers.ChoiceField(choices=['PRODUCAO', 'DOACAO', 'PERDA'])
    lote_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    justificativa = serializers.CharField(allow_blank=False, trim_whitespace=True)
    data_hora = serializers.DateTimeField(required=False)

    def validate(self, attrs):
        tipo_saida = attrs.get('tipo_saida')
        lote_id = attrs.get('lote_id')
        if tipo_saida == 'PERDA' and lote_id is None:
            raise serializers.ValidationError({
                'lote_id': 'Selecione o lote que est\u00e1 sendo baixado por perda ou vencimento.',
            })
        if tipo_saida != 'PERDA' and lote_id is not None:
            raise serializers.ValidationError({
                'lote_id': 'O lote s\u00f3 deve ser informado para sa\u00eddas por perda ou vencimento.',
            })
        return attrs


class CargaInicialSerializer(serializers.Serializer):
    item_generico_id = serializers.IntegerField(min_value=1)
    quantidade = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal('0.001'))
    justificativa = serializers.CharField(allow_blank=False, trim_whitespace=True)
    data_hora = serializers.DateTimeField(required=False)


class AjusteSerializer(serializers.Serializer):
    item_generico_id = serializers.IntegerField(min_value=1)
    quantidade_contada = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=Decimal('0'))
    justificativa = serializers.CharField(allow_blank=False, trim_whitespace=True)
    data_hora = serializers.DateTimeField(required=False)


class EstornoSerializer(serializers.Serializer):
    movimentacao_id = serializers.IntegerField(min_value=1)
    justificativa = serializers.CharField(allow_blank=False, trim_whitespace=True)
    data_hora = serializers.DateTimeField(required=False)


class LoteRecebimentoSerializer(serializers.Serializer):
    numero_lote = serializers.CharField(
        max_length=100,
        allow_blank=False,
        trim_whitespace=True,
    )
    data_validade = serializers.DateField()
    quantidade = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal('0.001'),
    )

    def validate_numero_lote(self, valor):
        numero_lote = valor.strip()
        if not numero_lote:
            raise serializers.ValidationError('Informe o n\u00famero do lote.')
        if numero_lote.casefold() == LoteEstoque.NUMERO_LOTE_LEGADO.casefold():
            raise serializers.ValidationError(
                'O identificador LEGADO \u00e9 reservado para saldos anteriores ao controle de lotes.'
            )
        return numero_lote


class ItemRecebimentoSerializer(serializers.Serializer):
    item_ordem_id = serializers.IntegerField(min_value=1)
    lotes = LoteRecebimentoSerializer(many=True, allow_empty=False)
    observacao = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_lotes(self, lotes):
        numeros_informados = set()
        for lote in lotes:
            numero_normalizado = lote['numero_lote'].strip().casefold()
            if numero_normalizado in numeros_informados:
                raise serializers.ValidationError(
                    'O mesmo lote foi informado mais de uma vez para este item.'
                )
            numeros_informados.add(numero_normalizado)
        return lotes


class RecebimentoSerializer(serializers.Serializer):
    ordem_id = serializers.IntegerField(min_value=1)
    data_entrada = serializers.DateTimeField(required=False)
    itens = ItemRecebimentoSerializer(many=True, allow_empty=False)

