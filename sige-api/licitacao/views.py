from urllib import request
from warnings import filters

from rest_framework import viewsets, filters
from rest_framework.response import Response
from licitacao.models import Licitacao, Ata, ItemAta
from licitacao.serializers import LicitacaoSerializer, AtaSerializer, ItemAtaSerializer, itensDaAtaSerializer
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
    serializer_class = ValorEmpenhoSerializer

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
    serializer_class = itensDaAtaSerializer

    def get_queryset(self):
        ata_id = self.request.query_params.get('ata_id')
        return ItemAta.objects.filter(ata_id=ata_id)