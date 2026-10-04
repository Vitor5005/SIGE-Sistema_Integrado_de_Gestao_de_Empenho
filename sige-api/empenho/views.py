from decimal import Decimal

from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from empenho.models import Empenho, ItemEmpenho,  OperacaoItem, SolicitacaoReforco
from empenho.serializers import EmpenhoInsertSerializer, EmpenhoSerializer, EmpenhoUpdateSerializer, ItemEmpenhoInsertSerializer, ItemEmpenhoSerializer, OperacaoItemInsertSerializer, OperacaoItemSerializer, SolicitacaoReforcoSerializer
from empenho.services import (
    atender_solicitacao_reforco,
    recusar_solicitacao_reforco,
    registrar_operacao_item,
    saldo_disponivel_ata,
    solicitar_reforco,
)
from utils.mixins import (
    AuditoriaRBACMixin,
    BaseFiltroMixin,
    EscopoPorPapelMixin,
    FiltroQueryParamMixin,
    SerializerEscritaMixin,
)
from utils.rbac import Acao, Papel, Recurso
class EmpenhoViewSet(AuditoriaRBACMixin, BaseFiltroMixin, SerializerEscritaMixin, viewsets.ModelViewSet):
    queryset = Empenho.objects.all()
    serializer_class = EmpenhoSerializer
    serializer_class_escrita = EmpenhoInsertSerializer
    rbac_resource = Recurso.EMPENHO
    rbac_action_map = {'resumo_financeiro': Acao.CONSULTAR}
    search_fields = [
        'codigo',
        'ata__numero_ata',
        'ata__licitacao__numero_licitacao',
        'ata__fornecedor__razao_social',
        'ata__fornecedor__nome_fantasia',
        'ata__fornecedor__cnpj',
    ]
    filterset_fields = {
        'ata__id': ['exact'], 
        'ata__licitacao__id': ['exact'],
        'valor_total': ['exact', 'gte', 'lte'],
        'saldo_utilizado': ['exact', 'gte', 'lte'],
    }

    @action(detail=False, methods=['get'], url_path='resumo-financeiro')
    def resumo_financeiro(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        totais = queryset.aggregate(
            valor_empenhado=Sum('valor_total'),
            valor_utilizado=Sum('saldo_utilizado'),
        )
        valor_empenhado = totais['valor_empenhado'] or Decimal('0.00')
        valor_utilizado = totais['valor_utilizado'] or Decimal('0.00')
        valor_disponivel = valor_empenhado - valor_utilizado

        return Response({
            'valor_empenhado': f'{valor_empenhado:.2f}',
            'valor_utilizado': f'{valor_utilizado:.2f}',
            'valor_disponivel': f'{valor_disponivel:.2f}',
        })
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EmpenhoInsertSerializer
        if self.action in ['update', 'partial_update']:
            return EmpenhoUpdateSerializer
        return EmpenhoSerializer
   
    ordering_fields = ['valor_total', 'saldo_utilizado', 'codigo']
    ordering = ['-id']  

    
class ItemDoEmpehoViewSet(AuditoriaRBACMixin, FiltroQueryParamMixin, viewsets.ModelViewSet):
    queryset = ItemEmpenho.objects.all()
    serializer_class = ItemEmpenhoSerializer
    rbac_resource = Recurso.ITEM_EMPENHO
    pagination_class = None
    filtros_query_param = {'empenho_id': 'empenho_id'}
    filtros_obrigatorios = True

class ItemEmpenhoViewSet(AuditoriaRBACMixin, SerializerEscritaMixin, viewsets.ModelViewSet):
    queryset = ItemEmpenho.objects.all()
    serializer_class = ItemEmpenhoSerializer
    serializer_class_escrita = ItemEmpenhoInsertSerializer
    rbac_resource = Recurso.ITEM_EMPENHO

class OperacaoDoEmpenhoViewSet(AuditoriaRBACMixin, FiltroQueryParamMixin, viewsets.ModelViewSet):
    queryset = OperacaoItem.objects.all()
    serializer_class = OperacaoItemSerializer
    rbac_resource = Recurso.OPERACAO_EMPENHO
    pagination_class = None
    filtros_query_param = {'empenho_id': 'item_empenho__empenho_id'}

class OperacaoItemViewSet(AuditoriaRBACMixin, BaseFiltroMixin, SerializerEscritaMixin, viewsets.ModelViewSet):
    queryset = OperacaoItem.objects.all()
    serializer_class = OperacaoItemSerializer
    serializer_class_escrita = OperacaoItemInsertSerializer
    rbac_resource = Recurso.OPERACAO_EMPENHO
    http_method_names = ['get', 'post', 'head', 'options']

    def create(self, request, *args, **kwargs):
        serializer = OperacaoItemInsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data
        operacao = registrar_operacao_item(
            item_empenho_id=dados['item_empenho'].pk,
            tipo=dados['tipo'],
            valor=dados['valor'],
            data=dados['data'],
        )
        return Response(OperacaoItemSerializer(operacao).data, status=201)

    search_fields = ['tipo', 'item_empenho__item_ata__item_generico__descricao']
    filterset_fields = {
        'tipo': ['exact'], 
        'item_empenho__id': ['exact'],
        'data': ['exact', 'gte', 'lte'],
        'valor': ['exact', 'gte', 'lte'],
    }

    ordering_fields = ['data', 'valor']
    ordering = ['-data']



class SolicitacaoReforcoViewSet(
    AuditoriaRBACMixin, BaseFiltroMixin, EscopoPorPapelMixin, viewsets.ReadOnlyModelViewSet
):
    """
    Pedidos de reforço feitos pelo Nutricionista ao Diretor.
    O Nutricionista vê apenas os próprios pedidos; o Diretor vê todos.
    """
    queryset = SolicitacaoReforco.objects.select_related(
        'item_empenho__empenho', 'item_empenho__item_ata__item_generico',
        'solicitante', 'respondida_por',
    )
    serializer_class = SolicitacaoReforcoSerializer
    rbac_resource = Recurso.SOLICITACAO_REFORCO
    escopo_por_papel = {Papel.NUTRICIONISTA: lambda usuario: Q(solicitante=usuario)}
    rbac_action_map = {
        'create': Acao.CADASTRAR,
        'saldo': Acao.CADASTRAR,
        'atender': Acao.REFORCAR_EMPENHO,
        'recusar': Acao.ALTERAR_STATUS,
        'marcar_vista': Acao.CONSULTAR,
    }
    filterset_fields = {
        'status': ['exact', 'in'],
        'item_empenho__empenho__id': ['exact'],
        'vista_pelo_solicitante': ['exact'],
    }
    ordering_fields = ['data_solicitacao', 'data_resposta']
    ordering = ['-data_solicitacao', '-id']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        solicitacao = solicitar_reforco(
            item_empenho_id=serializer.validated_data['item_empenho'].pk,
            quantidade=serializer.validated_data['quantidade'],
            justificativa=serializer.validated_data['justificativa'],
            usuario=request.user,
        )
        return Response(self.get_serializer(solicitacao).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def saldo(self, request):
        """Saldo disponível na ARP para o item do empenho informado (?item_empenho=ID)."""
        item_empenho = get_object_or_404(
            ItemEmpenho.objects.select_related('item_ata'),
            pk=request.query_params.get('item_empenho'),
        )
        return Response({
            'item_empenho': item_empenho.pk,
            'saldo_disponivel': f'{saldo_disponivel_ata(item_empenho.item_ata):.2f}',
        })

    @action(detail=True, methods=['post'])
    def atender(self, request, pk=None):
        solicitacao = atender_solicitacao_reforco(
            solicitacao_id=self.get_object().pk,
            usuario=request.user,
            resposta=request.data.get('resposta', ''),
        )
        return Response(self.get_serializer(solicitacao).data)

    @action(detail=True, methods=['post'])
    def recusar(self, request, pk=None):
        solicitacao = recusar_solicitacao_reforco(
            solicitacao_id=self.get_object().pk,
            usuario=request.user,
            resposta=request.data.get('resposta', ''),
        )
        return Response(self.get_serializer(solicitacao).data)

    @action(detail=True, methods=['post'], url_path='marcar-vista')
    def marcar_vista(self, request, pk=None):
        """O solicitante confirma que viu a resposta do Diretor (remove o aviso do sino)."""
        solicitacao = self.get_object()
        if solicitacao.solicitante_id != request.user.pk:
            return Response(
                {'detail': 'Somente quem fez a solicitação pode marcá-la como vista.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not solicitacao.vista_pelo_solicitante:
            solicitacao.vista_pelo_solicitante = True
            solicitacao.save(update_fields=['vista_pelo_solicitante'])
        return Response(self.get_serializer(solicitacao).data)
