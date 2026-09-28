from decimal import Decimal

from django.utils import timezone
from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from empenho.models import Empenho, ItemEmpenho, OperacaoItem, SolicitacaoReforco
from empenho.serializers import EmpenhoInsertSerializer, EmpenhoSerializer, EmpenhoUpdateSerializer, ItemEmpenhoInsertSerializer, ItemEmpenhoSerializer, OperacaoItemInsertSerializer, OperacaoItemSerializer, SolicitacaoReforcoSerializer
from empenho.services import registrar_operacao_item
from licitacao.views import BaseFiltroMixin
from utils.audit import AuditoriaRBACMixin
from utils.permissions import RBACPermission
from utils.rbac import Acao, Papel, Recurso
class EmpenhoViewSet(AuditoriaRBACMixin, BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = Empenho.objects.all()
    serializer_class = EmpenhoSerializer
    permission_classes = [RBACPermission]
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

    
class ItemDoEmpehoViewSet(AuditoriaRBACMixin, viewsets.ModelViewSet):
    queryset = ItemEmpenho.objects.all()
    serializer_class = ItemEmpenhoSerializer
    permission_classes = [RBACPermission]
    rbac_resource = Recurso.ITEM_EMPENHO
    pagination_class = None
    
    def get_queryset(self):
        empenho_id = self.request.query_params.get('empenho_id')
        return ItemEmpenho.objects.filter(empenho_id=empenho_id)

class ItemEmpenhoViewSet(AuditoriaRBACMixin, viewsets.ModelViewSet):
    queryset = ItemEmpenho.objects.all()
    serializer_class = ItemEmpenhoSerializer
    permission_classes = [RBACPermission]
    rbac_resource = Recurso.ITEM_EMPENHO
    
    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return ItemEmpenhoInsertSerializer
        
        return ItemEmpenhoSerializer
    
class OperacaoDoEmpenhoViewSet(AuditoriaRBACMixin, viewsets.ModelViewSet):
    queryset = OperacaoItem.objects.all()
    serializer_class = OperacaoItemSerializer
    permission_classes = [RBACPermission]
    rbac_resource = Recurso.OPERACAO_EMPENHO
    pagination_class = None
    
    def get_queryset(self):
        empenho_id = self.request.query_params.get('empenho_id')
        if empenho_id:
            return OperacaoItem.objects.filter(item_empenho__empenho_id=empenho_id)
        return OperacaoItem.objects.all() 

class OperacaoItemViewSet(AuditoriaRBACMixin, viewsets.ModelViewSet):
    queryset = OperacaoItem.objects.all()
    serializer_class = OperacaoItemSerializer
    permission_classes = [RBACPermission]
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
    
    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return OperacaoItemInsertSerializer
        
        return OperacaoItemSerializer
    
    search_fields = ['tipo', 'item_empenho__item_ata__item_generico__descricao']
    filterset_fields = {
        'tipo': ['exact'], 
        'item_empenho__id': ['exact'],
        'data': ['exact', 'gte', 'lte'],
        'valor': ['exact', 'gte', 'lte'],
    }

    ordering_fields = ['data', 'valor']
    ordering = ['-data']


class SolicitacaoReforcoViewSet(AuditoriaRBACMixin, BaseFiltroMixin, viewsets.ModelViewSet):
    queryset = SolicitacaoReforco.objects.select_related(
        'item_empenho__empenho',
        'item_empenho__item_ata__item_generico',
        'solicitante',
        'ciente_por',
    )
    serializer_class = SolicitacaoReforcoSerializer
    permission_classes = [RBACPermission]
    rbac_resource = Recurso.SOLICITACAO_REFORCO
    rbac_action_map = {
        'create': Acao.SOLICITAR_REFORCO,
        'ciente': Acao.ALTERAR_STATUS,
    }
    http_method_names = ['get', 'post', 'head', 'options']
    filterset_fields = {
        'status': ['exact'],
        'item_empenho__id': ['exact'],
        'item_empenho__empenho__id': ['exact'],
    }
    ordering_fields = ['data_solicitacao', 'id']
    ordering = ['-data_solicitacao', '-id']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.papel == Papel.NUTRICIONISTA:
            return queryset.filter(solicitante=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(solicitante=self.request.user)

    @action(detail=True, methods=['post'], url_path='ciente')
    def ciente(self, request, *args, **kwargs):
        solicitacao = self.get_object()
        if solicitacao.status != SolicitacaoReforco.Status.ABERTA:
            raise ValidationError({
                'status': 'A solicitação de reforço já recebeu ciência.'
            })

        solicitacao.status = SolicitacaoReforco.Status.CIENTE
        solicitacao.ciente_por = request.user
        solicitacao.data_ciencia = timezone.now()
        solicitacao.save(update_fields=['status', 'ciente_por', 'data_ciencia'])

        return Response(self.get_serializer(solicitacao).data)
