from rest_framework import viewsets
from cadastro.models import Endereco, Fornecedor, ItemGenerico
from cadastro.serializers import EnderecoSerializer, FornecedorSerializer, FornecedorCreateSerializer, ItemGenericoSerializer
from utils.mixins import AuditoriaRBACMixin, BaseFiltroMixin, SerializerEscritaMixin
from utils.rbac import Recurso
class EnderecoViewSet(AuditoriaRBACMixin, viewsets.ModelViewSet):
    queryset = Endereco.objects.all()
    serializer_class = EnderecoSerializer
    rbac_resource = Recurso.ENDERECO

class FornecedorViewSet(AuditoriaRBACMixin, BaseFiltroMixin, SerializerEscritaMixin, viewsets.ModelViewSet):
    queryset = Fornecedor.objects.all()
    serializer_class = FornecedorSerializer
    serializer_class_escrita = FornecedorCreateSerializer
    rbac_resource = Recurso.FORNECEDOR

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
class ItemGenericoViewSet(AuditoriaRBACMixin, BaseFiltroMixin, viewsets.ModelViewSet):
    queryset = ItemGenerico.objects.all()
    serializer_class = ItemGenericoSerializer
    rbac_resource = Recurso.GENERO_ALIMENTICIO

    
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

