from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.response import Response
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.ata_set.exists():
            return Response(
                {'detail': 'Não é possível excluir este fornecedor porque existem ARPs vinculadas.'},
                status=status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            endereco_id = instance.endereco_id
            self.perform_destroy(instance)

            if endereco_id and not Fornecedor.objects.filter(endereco_id=endereco_id).exists():
                Endereco.objects.filter(id=endereco_id).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ItemGenericoViewSet(AuditoriaRBACMixin, BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = ItemGenerico.objects.all()
    serializer_class = ItemGenericoSerializer
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        possui_estoque = hasattr(instance, 'estoque')

        if instance.itemata_set.exists() or possui_estoque:
            return Response(
                {
                    'detail': (
                        'Não é possível excluir este gênero alimentício porque ele já está sendo utilizado '
                        'em uma ARP ou possui registro de estoque.'
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        return super().destroy(request, *args, **kwargs)

