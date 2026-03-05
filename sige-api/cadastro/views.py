from rest_framework import viewsets
from cadastro.models import Endereco, Fornecedor, ItemGenerico
from cadastro.serializers import EnderecoSerializer, FornecedorSerializer, FornecedorCreateSerializer, ItemGenericoSerializer

class EnderecoViewSet(viewsets.ModelViewSet):
    queryset = Endereco.objects.all()
    serializer_class = EnderecoSerializer

class FornecedorViewSet(viewsets.ModelViewSet):
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer
    
    def get_serializer_class(self):
        
        if self.action in ['create', 'update']:
            return FornecedorCreateSerializer
        
        return FornecedorSerializer
    

class ItemGenericoViewSet(viewsets.ModelViewSet):
    queryset = ItemGenerico.objects.all()
    serializer_class = ItemGenericoSerializer

