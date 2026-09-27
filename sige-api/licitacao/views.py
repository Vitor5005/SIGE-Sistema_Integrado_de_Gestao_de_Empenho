from urllib import request
#from warnings import filters

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from licitacao.models import Licitacao, Ata, ItemAta
from licitacao.serializers import AtaInsertSerializer, ItemAtaInsertSerializer, LicitacaoSerializer, AtaSerializer, ItemAtaSerializer, ItensEmpenhoDaAtaSerializer
from empenho.serializers import ValorEmpenhoSerializer
from empenho.models import Empenho, ItemEmpenho
from utils.audit import AuditoriaRBACMixin
from utils.permissions import RBACPermission
from utils.rbac import Acao, Recurso
class BaseFiltroMixin:
    """
    Mixin de configuração padrão de busca, filtro e ordenação
    a qualquer ModelViewSet que precisar.
    """
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    
class LicitacaoViewSet(AuditoriaRBACMixin, BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = Licitacao.objects.all()
    serializer_class = LicitacaoSerializer
    permission_classes = [RBACPermission]
    rbac_resource = Recurso.LICITACAO
    rbac_action_map = {'definir_atual': Acao.DEFINIR_ATUAL}
    # filter_backends = [
    #     DjangoFilterBackend,
    #     filters.SearchFilter,
    #     filters.OrderingFilter
    # ]

    search_fields = ['numero_licitacao','descricao']
    filterset_fields = {
        'data_abertura':['exact', 'gte', 'lte'],
        'validade':['exact', 'gte', 'lte'],
        'atual': ['exact'],
    }
    ordering_fields = ['data_abertura','validade']
    ordering = ['-data_abertura']

    @action(detail=True, methods=['post'], url_path='definir-atual')
    def definir_atual(self, request, pk=None):
        licitacao = self.get_object()
        licitacao.definir_como_atual()
        return Response(self.get_serializer(licitacao).data)

class AtaViewSet(AuditoriaRBACMixin, BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = Ata.objects.all()
    serializer_class = AtaSerializer
    permission_classes = [RBACPermission]
    rbac_resource = Recurso.ATA

    def get_serializer_class(self):
        
        if self.action in ['create', 'update']:
            return AtaInsertSerializer
        
        return AtaSerializer

    search_fields = ['numero_ata']
    filterset_fields = {
        'licitacao__id': ['exact'],
        'fornecedor__id': ['exact'],
        'ata_saldo_total': ['exact', 'gte', 'lte'],
    }
    ordering_fields = ['ata_saldo_total', 'numero_ata']
    ordering = ['-ata_saldo_total']

class ItemAtaViewSet(AuditoriaRBACMixin, viewsets.ModelViewSet):
    queryset = ItemAta.objects.all()
    serializer_class = ItemAtaSerializer
    permission_classes = [RBACPermission]
    rbac_resource = Recurso.ITEM_ATA
    
    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return ItemAtaInsertSerializer
        
        return ItemAtaSerializer

class ValorDoEmpenhoViewSet(AuditoriaRBACMixin, viewsets.ModelViewSet):
    serializer_class = ValorEmpenhoSerializer
    permission_classes = [RBACPermission]
    rbac_resource = Recurso.EMPENHO

    def get_queryset(self):
        ata_id = self.request.query_params.get('ata_id')
        return Empenho.objects.filter(ata_id=ata_id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # Pega o primeiro elemento da lista
        instance = queryset.first()
        
        if instance:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        
        # Retorna um objeto vazio ou 404 se preferir
        return Response({})
    
class ItensDaAtaViewSet(AuditoriaRBACMixin, viewsets.ModelViewSet):
    serializer_class = ItensEmpenhoDaAtaSerializer
    permission_classes = [RBACPermission]
    rbac_resource = Recurso.ITEM_EMPENHO
    pagination_class = None

    def get_queryset(self):
        ata_id = self.request.query_params.get('ata_id')
        return ItemEmpenho.objects.filter(empenho__ata_id=ata_id)
