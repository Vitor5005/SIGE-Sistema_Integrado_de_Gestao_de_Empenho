from decimal import Decimal

from rest_framework import serializers

from estoque.models import Estoque, LoteEstoque, MovimentacaoEstoque, MovimentacaoLote
from utils.estoque_services import (
    STATUS_VALIDADE_DESCRICOES,
    dias_para_data_validade,
    dias_para_validade,
    lote_vencido,
    saldo_utilizavel_estoque,
    status_data_validade,
    status_lote_validade,
)


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
    lotes_vencidos = serializers.IntegerField(read_only=True, default=0)
    lotes_vence_hoje = serializers.IntegerField(read_only=True, default=0)
    lotes_criticos = serializers.IntegerField(read_only=True, default=0)
    lotes_atencao = serializers.IntegerField(read_only=True, default=0)
    proxima_validade = serializers.DateField(read_only=True, allow_null=True)
    dias_para_proxima_validade = serializers.SerializerMethodField()
    status_proxima_validade = serializers.SerializerMethodField()
    status_proxima_validade_descricao = serializers.SerializerMethodField()

    def get_saldo_utilizavel(self, estoque):
        if hasattr(estoque, 'lotes_utilizaveis_prefetch'):
            return sum(
                (lote.saldo_atual for lote in estoque.lotes_utilizaveis_prefetch),
                Decimal('0.000'),
            ).quantize(Decimal('0.001'))
        return saldo_utilizavel_estoque(estoque)

    def get_dias_para_proxima_validade(self, estoque):
        return dias_para_data_validade(getattr(estoque, 'proxima_validade', None))

    def get_status_proxima_validade(self, estoque):
        proxima_validade = getattr(estoque, 'proxima_validade', None)
        if proxima_validade is None:
            return None
        return status_data_validade(proxima_validade)

    def get_status_proxima_validade_descricao(self, estoque):
        status = self.get_status_proxima_validade(estoque)
        return STATUS_VALIDADE_DESCRICOES[status] if status is not None else None

    class Meta:
        model = Estoque
        fields = (
            'id', 'item_generico_id', 'catmat', 'descricao', 'unidade_medida',
            'categoria', 'categoria_descricao', 'conteudo_embalagem',
            'unidade_embalagem', 'imagem', 'saldo_atual', 'saldo_utilizavel', 'data_atualizacao',
            'possui_carga_inicial', 'lotes_vencidos', 'lotes_vence_hoje',
            'lotes_criticos', 'lotes_atencao', 'proxima_validade',
            'dias_para_proxima_validade', 'status_proxima_validade',
            'status_proxima_validade_descricao',
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


class AlocacaoLoteMovimentacaoSerializer(serializers.ModelSerializer):
    lote_id = serializers.IntegerField(read_only=True)
    numero_lote = serializers.CharField(source='lote.numero_lote', read_only=True)
    data_validade = serializers.DateField(source='lote.data_validade', read_only=True, allow_null=True)
    legado = serializers.BooleanField(source='lote.legado', read_only=True)

    class Meta:
        model = MovimentacaoLote
        fields = (
            'lote_id', 'numero_lote', 'data_validade', 'legado',
            'quantidade', 'saldo_lote_resultante',
        )
        read_only_fields = fields


class MovimentacaoEstoqueExtratoSerializer(MovimentacaoEstoqueSerializer):
    inventario_id = serializers.IntegerField(
        source='item_inventario.inventario_id',
        read_only=True,
        allow_null=True,
    )
    alocacoes_lote = AlocacaoLoteMovimentacaoSerializer(many=True, read_only=True)

    class Meta(MovimentacaoEstoqueSerializer.Meta):
        fields = MovimentacaoEstoqueSerializer.Meta.fields + (
            'inventario_id',
            'alocacoes_lote',
        )
        read_only_fields = fields


def _referencias_fornecedor(movimentacao):
    item_ordem = getattr(movimentacao, 'item_ordem', None)
    if item_ordem is None:
        return {
            'ordem_codigo': None,
            'fornecedor_nome': None,
            'empenho_codigo': None,
            'ata_numero': None,
        }

    ordem = getattr(item_ordem, 'ordem_entrega', None)
    item_empenho = getattr(item_ordem, 'item_empenho', None)
    empenho = getattr(item_empenho, 'empenho', None)
    ata = getattr(empenho, 'ata', None)
    fornecedor = getattr(ata, 'fornecedor', None)
    return {
        'ordem_codigo': getattr(ordem, 'codigo', None),
        'fornecedor_nome': (
            (getattr(fornecedor, 'nome_fantasia', None) or getattr(fornecedor, 'razao_social', None))
            if fornecedor is not None
            else None
        ),
        'empenho_codigo': getattr(empenho, 'codigo', None),
        'ata_numero': getattr(ata, 'numero_ata', None),
    }


class HistoricoMovimentacaoLoteSerializer(serializers.ModelSerializer):
    movimentacao_id = serializers.IntegerField(read_only=True)
    data_hora = serializers.DateTimeField(source='movimentacao.data_hora', read_only=True)
    tipo = serializers.CharField(source='movimentacao.tipo', read_only=True)
    tipo_descricao = serializers.SerializerMethodField()
    sentido = serializers.CharField(source='movimentacao.sentido', read_only=True)
    quantidade_movimentacao = serializers.DecimalField(
        source='movimentacao.quantidade', max_digits=12, decimal_places=3, read_only=True,
    )
    quantidade_lote = serializers.DecimalField(
        source='quantidade', max_digits=12, decimal_places=3, read_only=True,
    )
    saldo_estoque_resultante = serializers.DecimalField(
        source='movimentacao.saldo_resultante', max_digits=12, decimal_places=3, read_only=True,
    )
    observacao = serializers.CharField(source='movimentacao.observacao', read_only=True, allow_null=True)
    usuario_nome = serializers.CharField(source='movimentacao.usuario.username', read_only=True)
    papel = serializers.CharField(source='movimentacao.papel', read_only=True)
    ordem_codigo = serializers.SerializerMethodField()
    fornecedor_nome = serializers.SerializerMethodField()
    cardapio_id = serializers.SerializerMethodField()
    inventario_id = serializers.SerializerMethodField()
    movimentacao_estornada_id = serializers.IntegerField(
        source='movimentacao.movimentacao_estornada_id', read_only=True, allow_null=True,
    )

    class Meta:
        model = MovimentacaoLote
        fields = (
            'movimentacao_id', 'data_hora', 'tipo', 'tipo_descricao', 'sentido',
            'quantidade_movimentacao', 'quantidade_lote', 'saldo_estoque_resultante',
            'saldo_lote_resultante', 'observacao', 'usuario_nome', 'papel',
            'ordem_codigo', 'fornecedor_nome', 'cardapio_id', 'inventario_id',
            'movimentacao_estornada_id',
        )
        read_only_fields = fields

    def get_tipo_descricao(self, alocacao):
        return alocacao.movimentacao.get_tipo_display()

    def get_ordem_codigo(self, alocacao):
        return _referencias_fornecedor(alocacao.movimentacao)['ordem_codigo']

    def get_fornecedor_nome(self, alocacao):
        return _referencias_fornecedor(alocacao.movimentacao)['fornecedor_nome']

    def get_cardapio_id(self, alocacao):
        item_cardapio = alocacao.movimentacao.item_cardapio
        return item_cardapio.cardapio_id if item_cardapio is not None else None

    def get_inventario_id(self, alocacao):
        item_inventario = alocacao.movimentacao.item_inventario
        return item_inventario.inventario_id if item_inventario is not None else None


class LoteSaidaSerializer(serializers.ModelSerializer):
    vencido = serializers.SerializerMethodField()

    class Meta:
        model = LoteEstoque
        fields = ('id', 'numero_lote', 'data_validade', 'saldo_atual', 'legado', 'vencido')
        read_only_fields = fields

    def get_vencido(self, lote):
        return lote_vencido(lote)


class LoteInventarioSerializer(serializers.ModelSerializer):
    vencido = serializers.SerializerMethodField()

    class Meta:
        model = LoteEstoque
        fields = ('id', 'numero_lote', 'data_validade', 'saldo_atual', 'legado', 'vencido')
        read_only_fields = fields

    def get_vencido(self, lote):
        return lote_vencido(lote)


class LoteValidadeSerializer(serializers.ModelSerializer):
    estoque_id = serializers.IntegerField(read_only=True)
    item_generico_id = serializers.IntegerField(source='estoque.item_generico_id', read_only=True)
    catmat = serializers.CharField(source='estoque.item_generico.catmat', read_only=True)
    descricao = serializers.CharField(source='estoque.item_generico.descricao', read_only=True)
    unidade_medida = serializers.CharField(source='estoque.item_generico.unidade_medida', read_only=True)
    categoria = serializers.CharField(source='estoque.item_generico.categoria', read_only=True)
    categoria_descricao = serializers.CharField(
        source='estoque.item_generico.get_categoria_display', read_only=True
    )
    dias_para_validade = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    status_descricao = serializers.SerializerMethodField()

    class Meta:
        model = LoteEstoque
        fields = (
            'id', 'estoque_id', 'item_generico_id', 'catmat', 'descricao', 'unidade_medida',
            'categoria', 'categoria_descricao', 'numero_lote', 'data_validade', 'saldo_atual',
            'legado', 'dias_para_validade', 'status', 'status_descricao',
        )
        read_only_fields = fields

    def get_dias_para_validade(self, lote):
        return dias_para_validade(lote)

    def get_status(self, lote):
        return status_lote_validade(lote)

    def get_status_descricao(self, lote):
        return STATUS_VALIDADE_DESCRICOES[self.get_status(lote)]


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
            raise serializers.ValidationError('Informe o número do lote.')
        if numero_lote.casefold() == LoteEstoque.NUMERO_LOTE_LEGADO.casefold():
            raise serializers.ValidationError(
                'O identificador LEGADO é reservado para saldos anteriores ao controle de lotes.'
            )
        return numero_lote


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
    lotes = LoteRecebimentoSerializer(many=True, allow_empty=False)
    justificativa = serializers.CharField(allow_blank=False, trim_whitespace=True)
    data_hora = serializers.DateTimeField(required=False)

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


class LoteContagemInventarioSerializer(serializers.Serializer):
    lote_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    numero_lote = serializers.CharField(
        required=False,
        allow_blank=False,
        trim_whitespace=True,
        max_length=100,
    )
    data_validade = serializers.DateField(required=False)
    quantidade_contada = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal('0'),
    )

    def validate(self, attrs):
        lote_id = attrs.get('lote_id')
        possui_identidade_nova = (
            attrs.get('numero_lote') is not None
            or attrs.get('data_validade') is not None
        )
        quantidade_contada = attrs['quantidade_contada']
        if lote_id is not None:
            if possui_identidade_nova:
                raise serializers.ValidationError({
                    'lotes': 'Para lotes existentes informe apenas o lote e a quantidade contada.',
                })
            return attrs

        if not attrs.get('numero_lote') or attrs.get('data_validade') is None:
            raise serializers.ValidationError({
                'lotes': 'Informe o número e a data de validade do novo lote.',
            })
        if quantidade_contada <= Decimal('0.000'):
            raise serializers.ValidationError({
                'quantidade_contada': 'A quantidade de um novo lote deve ser maior que zero.',
            })
        if attrs['numero_lote'].strip().casefold() == LoteEstoque.NUMERO_LOTE_LEGADO.casefold():
            raise serializers.ValidationError({
                'numero_lote': (
                    'O identificador LEGADO é reservado para saldos anteriores ao controle de lotes.'
                ),
            })
        return attrs


class AjusteSerializer(serializers.Serializer):
    item_generico_id = serializers.IntegerField(min_value=1)
    lotes = LoteContagemInventarioSerializer(many=True, allow_empty=False)
    justificativa = serializers.CharField(allow_blank=False, trim_whitespace=True)
    data_hora = serializers.DateTimeField(required=False)

    def validate_lotes(self, lotes):
        lote_ids = set()
        numeros_novos = set()
        for lote in lotes:
            lote_id = lote.get('lote_id')
            if lote_id is not None:
                if lote_id in lote_ids:
                    raise serializers.ValidationError(
                        'O mesmo lote foi informado mais de uma vez para este item.'
                    )
                lote_ids.add(lote_id)
                continue
            numero_lote = lote['numero_lote'].strip().casefold()
            if numero_lote in numeros_novos:
                raise serializers.ValidationError(
                    'O mesmo lote foi informado mais de uma vez para este item.'
                )
            numeros_novos.add(numero_lote)
        return lotes


class EstornoSerializer(serializers.Serializer):
    movimentacao_id = serializers.IntegerField(min_value=1)
    justificativa = serializers.CharField(allow_blank=False, trim_whitespace=True)
    data_hora = serializers.DateTimeField(required=False)


class _LoteRecebimentoSerializerLegado(serializers.Serializer):
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

