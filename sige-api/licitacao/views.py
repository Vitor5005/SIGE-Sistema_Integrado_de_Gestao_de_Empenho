from urllib import request
from warnings import filters

from rest_framework import viewsets, filters
from licitacao.models import Licitacao, Ata, ItemAta
from licitacao.serializers import LicitacaoSerializer, AtaSerializer, ItemAtaSerializer
from empenho.serializers import ValorEmpenhoSerializer
from empenho.models import Empenho

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

class ValorDoEmpenhoViewSet(viewsets.ModelViewSet):
    
    def get_queryset(self):
        ata_id = self.request.query_params.get('ata_id')
        return Empenho.objects.filter(ata__id=ata_id)
    
    serializer_class = ValorEmpenhoSerializer