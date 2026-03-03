from rest_framework import viewsets
from empenho.models import Empenho, ItemEmpenho,  OperacaoItem
from empenho.serializers import EmpenhoSerializer, ItemEmpenhoSerializer, OperacaoItemSerializer

class EmpenhoViewSet(viewsets.ModelViewSet):
    queryset = Empenho.objects.all()
    serializer_class = EmpenhoSerializer

class ItemEmpenhoViewSet(viewsets.ModelViewSet):
    queryset = ItemEmpenho.objects.all()
    serializer_class = ItemEmpenhoSerializer

class OperacaoItemViewSet(viewsets.ModelViewSet):
    queryset = OperacaoItem.objects.all()
    serializer_class = OperacaoItemSerializer

    