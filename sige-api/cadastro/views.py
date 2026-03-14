from rest_framework import viewsets
from cadastro.models import Endereco, Fornecedor, ItemGenerico
from cadastro.serializers import EnderecoSerializer, FornecedorSerializer, FornecedorCreateSerializer, ItemGenericoSerializer
from licitacao.views import BaseFiltroMixin
from utils.permissions import IsAdmin,IsTecnico
class EnderecoViewSet(viewsets.ModelViewSet):
    queryset = Endereco.objects.all()
    serializer_class = EnderecoSerializer
    permission_classes = [IsAdmin|IsTecnico]

class FornecedorViewSet(BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer
    permission_classes = [IsAdmin|IsTecnico]
    
    def get_serializer_class(self):
        
        if self.action in ['create', 'update']:
            return FornecedorCreateSerializer
        
        return FornecedorSerializer
    
   
    search_fields = [
        'cnpj', 
        #'razao_social', 
        'nome_fantasia',
        'endereco__estado'
    ]

   
    filterset_fields = {
        'cnpj': ['exact'],
        'endereco__estado': ['exact'],
        'endereco__municipio': ['exact', 'icontains']
    }

    ordering_fields = ['nome_fantasia', 'cnpj']
    ordering = ['nome_fantasia']
class ItemGenericoViewSet(BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = ItemGenerico.objects.all()
    serializer_class = ItemGenericoSerializer
    permission_classes = [IsAdmin|IsTecnico]

    
    search_fields = [
        'catmat',       
        'descricao',    
    ]
    filterset_fields = {
        'catmat': ['exact'],               
        'unidade_medida': ['exact'],      
        'categoria': ['exact'],            
    }

    ordering_fields = ['catmat', 'descricao', 'categoria']
    ordering = ['descricao']

