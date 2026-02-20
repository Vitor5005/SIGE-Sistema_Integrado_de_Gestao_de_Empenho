from rest_framework import viewsets
from licitacao.models import Licitacao, Ata, ItemAta
from licitacao.serializers import LicitacaoSerializer, AtaSerializer, ItemAtaSerializer

class LicitacaoViewSet(viewsets.ModelViewSet):
    queryset = Licitacao.objects.all()
    serializer_class = LicitacaoSerializer

class AtaViewSet(viewsets.ModelViewSet):
    queryset = Ata.objects.all()
    serializer_class = AtaSerializer

class ItemAtaViewSet(viewsets.ModelViewSet):
    queryset = ItemAta.objects.all()
    serializer_class = ItemAtaSerializer
    