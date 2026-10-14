from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from cardapio.models import Cardapio, ItemCardapio
from cardapio.services import faltas_de_saldo


def _nome_usuario(usuario):
    if not usuario:
        return None
    return usuario.get_full_name() or usuario.username


class ItemCardapioSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    descricao = serializers.CharField(source='item_generico.descricao', read_only=True)
    catmat = serializers.CharField(source='item_generico.catmat', read_only=True)
    unidade_medida = serializers.CharField(source='item_generico.unidade_medida', read_only=True)
    conteudo_embalagem = serializers.DecimalField(
        source='item_generico.conteudo_embalagem', max_digits=10, decimal_places=3, read_only=True,
    )
    unidade_embalagem = serializers.CharField(source='item_generico.unidade_embalagem', read_only=True)
    quantidade_planejada = serializers.DecimalField(
        max_digits=12, decimal_places=3, min_value=Decimal('0.001'),
    )

    class Meta:
        model = ItemCardapio
        fields = (
            'id', 'ordem', 'secao', 'item_generico', 'descricao', 'catmat', 'unidade_medida',
            'conteudo_embalagem', 'unidade_embalagem', 'quantidade_planejada',
            'quantidade_liberada', 'quantidade_consumida', 'observacao',
        )
        read_only_fields = ('quantidade_liberada', 'quantidade_consumida')


class CardapioSerializer(serializers.ModelSerializer):
    itens = ItemCardapioSerializer(many=True)
    refeicao_descricao = serializers.CharField(source='get_refeicao_display', read_only=True)
    status_descricao = serializers.CharField(source='get_status_display', read_only=True)
    criado_por_nome = serializers.SerializerMethodField()
    aprovado_por_nome = serializers.SerializerMethodField()
    finalizado_por_nome = serializers.SerializerMethodField()

    class Meta:
        model = Cardapio
        fields = (
            'id', 'refeicao', 'refeicao_descricao', 'data', 'estimativa_pessoas', 'preparacoes',
            'observacoes', 'status', 'status_descricao', 'motivo_recusa', 'itens',
            'criado_por', 'criado_por_nome', 'criado_em', 'atualizado_em', 'enviado_em',
            'aprovado_por', 'aprovado_por_nome', 'aprovado_em', 'consumo_informado_em',
            'finalizado_por', 'finalizado_por_nome', 'finalizado_em',
        )
        read_only_fields = (
            'status', 'motivo_recusa', 'criado_por', 'criado_em', 'atualizado_em', 'enviado_em',
            'aprovado_por', 'aprovado_em', 'consumo_informado_em', 'finalizado_por', 'finalizado_em',
        )

    def get_criado_por_nome(self, cardapio):
        return _nome_usuario(cardapio.criado_por)

    def get_aprovado_por_nome(self, cardapio):
        return _nome_usuario(cardapio.aprovado_por)

    def get_finalizado_por_nome(self, cardapio):
        return _nome_usuario(cardapio.finalizado_por)

    def validate_preparacoes(self, valor):
        linhas = [linha.strip() for linha in (valor or '').splitlines() if linha.strip()]
        if not linhas:
            raise serializers.ValidationError('Informe ao menos uma preparação.')
        return '\n'.join(linhas)

    def validate(self, dados):
        instancia = self.instance
        if instancia is not None and not instancia.editavel:
            raise serializers.ValidationError(
                'O cardápio só pode ser alterado enquanto for rascunho ou após ser recusado.'
            )

        itens = dados.get('itens')
        if itens is not None:
            self._validar_itens_contra_estoque(itens)
        return dados

    def _validar_itens_contra_estoque(self, itens):
        """O cardápio é montado a partir do estoque: só gêneros com saldo, até o disponível."""
        if not itens:
            raise serializers.ValidationError({'itens': 'Adicione ao menos um gênero com saldo em estoque.'})

        planejado = defaultdict(Decimal)
        generos = {}
        for item in itens:
            genero = item['item_generico']
            planejado[genero.id] += item['quantidade_planejada']
            generos[genero.id] = genero

        faltas = faltas_de_saldo(planejado, generos, excluir_cardapio_id=getattr(self.instance, 'pk', None))
        if faltas:
            raise serializers.ValidationError({'itens': faltas})

    def _gravar_itens(self, cardapio, itens):
        cardapio.itens.all().delete()
        ItemCardapio.objects.bulk_create([
            ItemCardapio(
                cardapio=cardapio,
                ordem=item.get('ordem', indice),
                secao=(item.get('secao') or '').strip(),
                item_generico=item['item_generico'],
                quantidade_planejada=item['quantidade_planejada'],
                observacao=(item.get('observacao') or '').strip(),
            )
            for indice, item in enumerate(itens)
        ])

    @transaction.atomic
    def create(self, dados):
        itens = dados.pop('itens', [])
        cardapio = Cardapio.objects.create(**dados)
        self._gravar_itens(cardapio, itens)
        return cardapio

    @transaction.atomic
    def update(self, cardapio, dados):
        itens = dados.pop('itens', None)
        for campo, valor in dados.items():
            setattr(cardapio, campo, valor)
        cardapio.save()
        if itens is not None:
            self._gravar_itens(cardapio, itens)
        return cardapio


class CardapioResumoSerializer(serializers.ModelSerializer):
    """Versão enxuta para listagens e notificações."""
    refeicao_descricao = serializers.CharField(source='get_refeicao_display', read_only=True)
    status_descricao = serializers.CharField(source='get_status_display', read_only=True)
    criado_por_nome = serializers.SerializerMethodField()
    total_itens = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cardapio
        fields = (
            'id', 'refeicao', 'refeicao_descricao', 'data', 'estimativa_pessoas', 'status',
            'status_descricao', 'motivo_recusa', 'criado_por_nome', 'total_itens', 'atualizado_em',
        )

    def get_criado_por_nome(self, cardapio):
        return _nome_usuario(cardapio.criado_por)


class QuantidadesItensSerializer(serializers.Serializer):
    """Lista de {item, quantidade} usada na aprovação e no consumo real."""
    itens = serializers.ListField(child=serializers.DictField(), allow_empty=False)

    def validate_itens(self, itens):
        quantidades = {}
        for linha in itens:
            try:
                item_id = int(linha['item'])
            except (KeyError, TypeError, ValueError):
                raise serializers.ValidationError('Cada linha deve informar o item.')
            if 'quantidade' not in linha or linha['quantidade'] in (None, ''):
                raise serializers.ValidationError('Informe a quantidade de todos os itens.')
            quantidades[item_id] = linha['quantidade']
        return quantidades


class MotivoSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=500, trim_whitespace=True)
