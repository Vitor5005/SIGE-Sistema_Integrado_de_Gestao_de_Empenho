from collections import defaultdict
from decimal import Decimal

from django.db.models import Exists, OuterRef, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from empenho.models import ItemEmpenho, OperacaoItem
from estoque.models import Estoque, MovimentacaoEstoque
from estoque.serializers import (
    AjusteSerializer,
    CargaInicialSerializer,
    EstoqueSerializer,
    EstornoSerializer,
    MovimentacaoEstoqueSerializer,
    RecebimentoSerializer,
    SaidaSerializer,
)
from utils.estoque_services import (
    estornar_movimentacao,
    registrar_ajuste,
    registrar_carga_inicial,
    registrar_recebimento,
    registrar_saida,
)
from utils.mixins import BaseFiltroMixin, FiltroQueryParamMixin, RBACMixin
from utils.rbac import Acao, Recurso


class EstoqueViewSet(RBACMixin, BaseFiltroMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Estoque.objects.select_related('item_generico').annotate(
        possui_carga_inicial=Exists(MovimentacaoEstoque.objects.filter(
            estoque=OuterRef('pk'), tipo=MovimentacaoEstoque.Tipo.CARGA_INICIAL,
        )),
    )
    serializer_class = EstoqueSerializer
    rbac_resource = Recurso.ESTOQUE
    rbac_action_map = {
        'consolidado': Acao.CONSULTAR_CONSOLIDADO,
        'recebimentos': Acao.REGISTRAR_RECEBIMENTO,
        'saidas': Acao.REGISTRAR_SAIDA,
        'cargas_iniciais': Acao.REGISTRAR_CARGA_INICIAL,
        'ajustes': Acao.REGISTRAR_AJUSTE,
        'estornos': Acao.ESTORNAR,
    }
    search_fields = [
        'item_generico__catmat', 'item_generico__descricao',
        'item_generico__unidade_medida', 'item_generico__categoria',
    ]
    filterset_fields = {'item_generico__categoria': ['exact']}
    ordering_fields = ['item_generico__descricao', 'item_generico__categoria', 'saldo_atual']
    ordering = ['item_generico__descricao']

    @action(detail=False, methods=['get'])
    def consolidado(self, request):
        itens = ItemEmpenho.objects.select_related(
            'empenho', 'item_ata__item_generico'
        ).all().order_by('empenho__codigo', 'item_ata__item_generico__descricao')

        operacoes = defaultdict(lambda: Decimal('0.00'))
        for operacao in OperacaoItem.objects.values('item_empenho__item_ata_id', 'tipo', 'valor'):
            sinal = Decimal('-1') if operacao['tipo'] == 'anl' else Decimal('1')
            operacoes[operacao['item_empenho__item_ata_id']] += sinal * operacao['valor']

        saldos = dict(Estoque.objects.values_list('item_generico_id', 'saldo_atual'))
        dados = []
        for item in itens:
            item_ata = item.item_ata
            genero = item_ata.item_generico
            dados.append({
                'empenho_id': item.empenho_id,
                'empenho': item.empenho.codigo,
                'item_generico_id': genero.id,
                'catmat': genero.catmat,
                'descricao': genero.descricao,
                'unidade_medida': genero.unidade_medida,
                'saldo_ata': item_ata.quantidade_licitada - operacoes[item_ata.id],
                'saldo_empenho': item.quantidade_atual,
                'saldo_estoque': saldos.get(genero.id, Decimal('0.000')),
            })
        return Response(dados)

    def _executar(self, serializer_class, servico, request):
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        resultado = servico(usuario=request.user, **serializer.validated_data)
        movimento = resultado[1] if isinstance(resultado, tuple) else resultado
        if isinstance(movimento, list):
            dados = MovimentacaoEstoqueSerializer(movimento, many=True).data
        else:
            dados = MovimentacaoEstoqueSerializer(movimento).data
        return Response(dados, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def recebimentos(self, request):
        serializer = RecebimentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ordem, movimentos = registrar_recebimento(
            ordem_id=serializer.validated_data['ordem_id'],
            itens_recebidos=serializer.validated_data['itens'],
            data_entrada=serializer.validated_data.get('data_entrada'),
            usuario=request.user,
        )
        return Response({
            'ordem_id': ordem.id,
            'status': ordem.status,
            'valor_total_recebido': ordem.valor_total_executado,
            'movimentacoes': MovimentacaoEstoqueSerializer(movimentos, many=True).data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def saidas(self, request):
        return self._executar(SaidaSerializer, registrar_saida, request)

    @action(detail=False, methods=['post'], url_path='cargas-iniciais')
    def cargas_iniciais(self, request):
        return self._executar(CargaInicialSerializer, registrar_carga_inicial, request)

    @action(detail=False, methods=['post'])
    def ajustes(self, request):
        return self._executar(AjusteSerializer, registrar_ajuste, request)

    @action(detail=False, methods=['post'])
    def estornos(self, request):
        return self._executar(EstornoSerializer, estornar_movimentacao, request)


class MovimentacaoEstoqueViewSet(RBACMixin, BaseFiltroMixin, FiltroQueryParamMixin, viewsets.ReadOnlyModelViewSet):
    queryset = MovimentacaoEstoque.objects.select_related(
        'estoque__item_generico', 'usuario', 'item_ordem__ordem_entrega'
    ).all()
    serializer_class = MovimentacaoEstoqueSerializer
    rbac_resource = Recurso.MOVIMENTACAO_ESTOQUE
    rbac_action_map = {'list': Acao.CONSULTAR_EXTRATO, 'retrieve': Acao.CONSULTAR_EXTRATO}
    search_fields = ['estoque__item_generico__catmat', 'estoque__item_generico__descricao', 'observacao']
    ordering_fields = ['data_hora', 'quantidade', 'saldo_resultante']
    ordering = ['-data_hora', '-id']
    filtros_query_param = {
        'genero_id': 'estoque__item_generico_id',
        'data_inicio': 'data_hora__gte',
        'data_fim': 'data_hora__lte',
    }

