from rest_framework import viewsets
from cadastro.models import Endereco, Fornecedor, ItemGenerico
from cadastro.serializers import EnderecoSerializer, FornecedorSerializer, FornecedorCreateSerializer, ItemGenericoSerializer
from licitacao.views import BaseFiltroMixin
from utils.audit import AuditoriaRBACMixin
from utils.permissions import RBACPermission
from utils.rbac import Recurso
class EnderecoViewSet(AuditoriaRBACMixin, viewsets.ModelViewSet):
    queryset = Endereco.objects.all()
    serializer_class = EnderecoSerializer
    permission_classes = [RBACPermission]
    rbac_resource = Recurso.ENDERECO

class FornecedorViewSet(AuditoriaRBACMixin, BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer
    permission_classes = [RBACPermission]
    rbac_resource = Recurso.FORNECEDOR
    
    def get_serializer_class(self):
        
        if self.action in ['create', 'update']:
            return FornecedorCreateSerializer
        
        return FornecedorSerializer
    
   
    search_fields = [
        'cnpj',
        'razao_social',
        'nome_fantasia',
        'email',
        'endereco__municipio',
        'endereco__estado',
    ]

   
    filterset_fields = {
        'cnpj': ['exact'],
        'endereco__estado': ['exact'],
        'endereco__municipio': ['exact', 'icontains']
    }

    ordering_fields = ['nome_fantasia', 'cnpj']
    ordering = ['nome_fantasia']
class ItemGenericoViewSet(AuditoriaRBACMixin, BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = ItemGenerico.objects.all()
    serializer_class = ItemGenericoSerializer
    permission_classes = [RBACPermission]
    rbac_resource = Recurso.GENERO_ALIMENTICIO

    
    search_fields = [
        'catmat',       
        'descricao',    
    ]
    filterset_fields = {
        'catmat': ['exact'],               
        'unidade_medida': ['exact', 'in'],      
        'categoria': ['exact', 'in'],            
    }

    ordering_fields = ['catmat', 'descricao', 'categoria']
    ordering = ['descricao']

