from rest_framework import viewsets
from empenho.models import Empenho, ItemEmpenho,  OperacaoItem
from empenho.serializers import EmpenhoInsertSerializer, EmpenhoSerializer, ItemEmpenhoInsertSerializer, ItemEmpenhoSerializer, OperacaoItemSerializer
from licitacao.views import BaseFiltroMixin

class EmpenhoViewSet(BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = Empenho.objects.all()
    serializer_class = EmpenhoSerializer
    search_fields = ['codigo', 'ata__numero_ata']
    filterset_fields = {
        'ata__id': ['exact'], 
        'valor_total': ['exact', 'gte', 'lte'],
        'saldo_utilizado': ['exact', 'gte', 'lte'],
    }
    
    def get_serializer_class(self):
        
        if self.action in ['create', 'update']:
            return EmpenhoInsertSerializer
        
        return EmpenhoSerializer
   
    ordering_fields = ['valor_total', 'saldo_utilizado', 'codigo']
    ordering = ['-id']  

class ItemEmpenhoViewSet(viewsets.ModelViewSet):
    queryset = ItemEmpenho.objects.all()
    serializer_class = ItemEmpenhoSerializer
    
    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return ItemEmpenhoInsertSerializer
        
        return ItemEmpenhoSerializer

class OperacaoItemViewSet(viewsets.ModelViewSet):
    queryset = OperacaoItem.objects.all()
    serializer_class = OperacaoItemSerializer
    search_fields = ['tipo', 'item_empenho__item_ata__item_generico__descricao']
    filterset_fields = {
        'tipo': ['exact'], 
        'item_empenho__id': ['exact'],
        'data': ['exact', 'gte', 'lte'],
        'valor': ['exact', 'gte', 'lte'],
    }

    ordering_fields = ['data', 'valor']
    ordering = ['-data']
    