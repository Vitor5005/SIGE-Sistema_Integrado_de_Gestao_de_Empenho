from warnings import filters

from rest_framework import viewsets, filters
from licitacao.models import Licitacao, Ata, ItemAta
from licitacao.serializers import LicitacaoSerializer, AtaSerializer, ItemAtaSerializer

class LicitacaoViewSet(viewsets.ModelViewSet):
    queryset = Licitacao.objects.all()
    serializer_class = LicitacaoSerializer

class AtaViewSet(viewsets.ModelViewSet):
    queryset = Ata.objects.all()
    serializer_class = AtaSerializer

    filter_backends = [filters.SearchFilter]
    search_fields = ['licitacao__id']

class ItemAtaViewSet(viewsets.ModelViewSet):
    queryset = ItemAta.objects.all()
    serializer_class = ItemAtaSerializer

    