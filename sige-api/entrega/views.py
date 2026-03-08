from rest_framework import viewsets
from entrega.models import OrdemEntrega, ItemOrdem
from entrega.serializers import OrdemEntregaSerializer, ItemOrdemSerializer
from licitacao.views import BaseFiltroMixin
class EntregaViewSet(BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = OrdemEntrega.objects.all()
    serializer_class = OrdemEntregaSerializer

    search_fields = ['codigo', 'empenho__codigo']
    filterset_fields = {
        'status': ['exact'],                         
        'empenho__id': ['exact'],                    
        'data_emissao': ['exact', 'gte', 'lte'],     
        'data_entrega': ['exact', 'gte', 'lte', 'isnull'],  
        'valor_total_executado': ['exact', 'gte', 'lte']
    }

    ordering_fields = ['data_emissao', 'data_entrega', 'valor_total_executado']
    ordering = ['-data_emissao']
    
class PedidosDaOrdemViewSet(viewsets.ModelViewSet):
    queryset = ItemOrdem.objects.all()
    serializer_class = ItemOrdemSerializer
    
    def get_queryset(self):
            queryset = super().get_queryset()
            ordem_id = self.request.query_params.get('ordem_id')
            if ordem_id is not None:
                queryset = queryset.filter(ordem_entrega__id=ordem_id)
            return queryset
    
class ItemEntregaViewSet(viewsets.ModelViewSet):
    queryset = ItemOrdem.objects.all()
    serializer_class = ItemOrdemSerializer

    
    search_fields = ['observacao', 'ordem_entrega__codigo', 'item_empenho__item_ata__item_generico__descricao']

    filterset_fields = {
        'ordem_entrega__id': ['exact'],
        'item_empenho__id': ['exact'],
        'quantidade_solicitada': ['exact', 'gte', 'lte'],
        'quantidade_entregue': ['exact', 'gte', 'lte']
    }

    ordering_fields = ['quantidade_solicitada', 'quantidade_entregue']
    ordering = ['id']