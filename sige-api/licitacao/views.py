from urllib import request
#from warnings import filters

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, filters
from rest_framework.response import Response
from licitacao.models import Licitacao, Ata, ItemAta
from licitacao.serializers import AtaInsertSerializer, ItemAtaInsertSerializer, LicitacaoSerializer, AtaSerializer, ItemAtaSerializer, ItensEmpenhoDaAtaSerializer
from empenho.serializers import ValorEmpenhoSerializer
from empenho.models import Empenho, ItemEmpenho
from utils.permissions import IsAdmin,IsTecnico
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
    
class LicitacaoViewSet(BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = Licitacao.objects.all()
    serializer_class = LicitacaoSerializer
    permission_classes = [IsAdmin|IsTecnico]
    # filter_backends = [
    #     DjangoFilterBackend,
    #     filters.SearchFilter,
    #     filters.OrderingFilter
    # ]

    search_fields = ['numero_licitacao','descricao']
    filterset_fields = {
        'data_abertura':['exact', 'gte', 'lte'],
        'validade':['exact', 'gte', 'lte']
    }
    ordering_fields = ['data_abertura','validade']
    ordering = ['-data_abertura']

class AtaViewSet(BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = Ata.objects.all()
    serializer_class = AtaSerializer
    permission_classes = [IsAdmin|IsTecnico]

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

class ItemAtaViewSet(viewsets.ModelViewSet):
    queryset = ItemAta.objects.all()
    serializer_class = ItemAtaSerializer
    permission_classes = [IsAdmin|IsTecnico]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return ItemAtaInsertSerializer
        
        return ItemAtaSerializer

class ValorDoEmpenhoViewSet(viewsets.ModelViewSet):
    serializer_class = ValorEmpenhoSerializer
    permission_classes = [IsAdmin|IsTecnico]

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
    
class ItensDaAtaViewSet(viewsets.ModelViewSet):
    serializer_class = ItensEmpenhoDaAtaSerializer
    permission_classes = [IsAdmin|IsTecnico]
    pagination_class = None

    def get_queryset(self):
        ata_id = self.request.query_params.get('ata_id')
        return ItemEmpenho.objects.filter(empenho__ata_id=ata_id)