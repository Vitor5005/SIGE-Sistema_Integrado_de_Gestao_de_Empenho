from rest_framework import viewsets
from entrega.models import OrdemEntrega, ItemOrdem
from entrega.serializers import OrdemEntregaSerializer, ItemOrdemSerializer

class EntregaViewSet(viewsets.ModelViewSet):
    queryset = OrdemEntrega.objects.all()
    serializer_class = OrdemEntregaSerializer

class ItemEntregaViewSet(viewsets.ModelViewSet):
    queryset = ItemOrdem.objects.all()
    serializer_class = ItemOrdemSerializer