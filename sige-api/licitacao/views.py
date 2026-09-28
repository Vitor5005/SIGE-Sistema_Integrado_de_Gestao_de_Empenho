from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from licitacao.models import Licitacao, Ata, ItemAta
from licitacao.serializers import AtaInsertSerializer, AtaUpdateSerializer, ItemAtaInsertSerializer, LicitacaoSerializer, LicitacaoUpdateSerializer, AtaSerializer, ItemAtaSerializer, ItensEmpenhoDaAtaSerializer
from empenho.serializers import ValorEmpenhoSerializer
from empenho.models import Empenho, ItemEmpenho
from utils.mixins import AuditoriaRBACMixin, BaseFiltroMixin, FiltroQueryParamMixin, SerializerEscritaMixin
from utils.rbac import Acao, Recurso

class LicitacaoViewSet(AuditoriaRBACMixin, BaseFiltroMixin, viewsets.ModelViewSet):
    queryset = Licitacao.objects.all()
    serializer_class = LicitacaoSerializer
    rbac_resource = Recurso.LICITACAO
    rbac_action_map = {'definir_atual': Acao.DEFINIR_ATUAL}

    search_fields = ['numero_licitacao','descricao']
    filterset_fields = {
        'data_abertura':['exact', 'gte', 'lte'],
        'validade':['exact', 'gte', 'lte'],
        'atual': ['exact'],
    }
    ordering_fields = ['data_abertura','validade']
    ordering = ['-data_abertura']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return LicitacaoUpdateSerializer
        return LicitacaoSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.ata_set.exists():
            return Response(
                {'detail': 'Não é possível excluir esta licitação porque existem ARPs vinculadas.'},
                status=status.HTTP_409_CONFLICT
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='definir-atual')
    def definir_atual(self, request, pk=None):
        licitacao = self.get_object()
        licitacao.definir_como_atual()
        return Response(self.get_serializer(licitacao).data)

class AtaViewSet(AuditoriaRBACMixin, BaseFiltroMixin, SerializerEscritaMixin, viewsets.ModelViewSet):
    queryset = Ata.objects.all()
    serializer_class = AtaSerializer
    serializer_class_escrita = AtaInsertSerializer
    rbac_resource = Recurso.ATA

    def get_serializer_class(self):
        if self.action == 'create':
            return AtaInsertSerializer
        if self.action in ['update', 'partial_update']:
            return AtaUpdateSerializer
        return AtaSerializer

    search_fields = [
        'numero_ata',
        'licitacao__numero_licitacao',
        'fornecedor__razao_social',
        'fornecedor__nome_fantasia',
        'fornecedor__cnpj',
    ]
    filterset_fields = {
        'licitacao__id': ['exact'],
        'fornecedor__id': ['exact'],
        'ata_saldo_total': ['exact', 'gte', 'lte'],
    }
    ordering_fields = ['ata_saldo_total', 'numero_ata']
    ordering = ['-ata_saldo_total']

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.empenho_set.exists() or instance.itemata_set.exists():
            return Response(
                {'detail': 'Não é possível excluir esta ARP porque existem itens ou empenho vinculados.'},
                status=status.HTTP_409_CONFLICT
            )
        return super().destroy(request, *args, **kwargs)

class ItemAtaViewSet(AuditoriaRBACMixin, viewsets.ModelViewSet):
    queryset = ItemAta.objects.all()
    serializer_class = ItemAtaSerializer
    serializer_class_escrita = ItemAtaInsertSerializer
    rbac_resource = Recurso.ITEM_ATA

class ValorDoEmpenhoViewSet(AuditoriaRBACMixin, FiltroQueryParamMixin, viewsets.ModelViewSet):
    queryset = Empenho.objects.all()
    serializer_class = ValorEmpenhoSerializer
    rbac_resource = Recurso.EMPENHO
    filtros_query_param = {'ata_id': 'ata_id'}
    filtros_obrigatorios = True

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # Pega o primeiro elemento da lista
        instance = queryset.first()
        
        if instance:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        
        # Retorna um objeto vazio ou 404 se preferir
        return Response({})
    
class ItensDaAtaViewSet(AuditoriaRBACMixin, FiltroQueryParamMixin, viewsets.ModelViewSet):
    queryset = ItemEmpenho.objects.all()
    serializer_class = ItensEmpenhoDaAtaSerializer
    rbac_resource = Recurso.ITEM_EMPENHO
    pagination_class = None
    filtros_query_param = {'ata_id': 'empenho__ata_id'}
    filtros_obrigatorios = True
