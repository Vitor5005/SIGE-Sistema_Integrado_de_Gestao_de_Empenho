from decimal import Decimal

from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from empenho.models import Empenho, ItemEmpenho,  OperacaoItem
from empenho.serializers import EmpenhoInsertSerializer, EmpenhoSerializer, ItemEmpenhoInsertSerializer, ItemEmpenhoSerializer, OperacaoItemInsertSerializer, OperacaoItemSerializer
from licitacao.views import BaseFiltroMixin
from utils.permissions import IsAdmin,IsTecnico
class EmpenhoViewSet(BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = Empenho.objects.all()
    serializer_class = EmpenhoSerializer
    permission_classes = [IsAdmin|IsTecnico]
    search_fields = ['codigo', 'ata__numero_ata', 'ata__fornecedor__nome_fantasia']
    filterset_fields = {
        'ata__id': ['exact'], 
        'ata__licitacao__id': ['exact'],
        'valor_total': ['exact', 'gte', 'lte'],
        'saldo_utilizado': ['exact', 'gte', 'lte'],
    }

    @action(detail=False, methods=['get'], url_path='resumo-financeiro')
    def resumo_financeiro(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        totais = queryset.aggregate(
            valor_empenhado=Sum('valor_total'),
            valor_utilizado=Sum('saldo_utilizado'),
        )
        valor_empenhado = totais['valor_empenhado'] or Decimal('0.00')
        valor_utilizado = totais['valor_utilizado'] or Decimal('0.00')
        valor_disponivel = valor_empenhado - valor_utilizado

        return Response({
            'valor_empenhado': f'{valor_empenhado:.2f}',
            'valor_utilizado': f'{valor_utilizado:.2f}',
            'valor_disponivel': f'{valor_disponivel:.2f}',
        })
    
    def get_serializer_class(self):
        
        if self.action in ['create', 'update']:
            return EmpenhoInsertSerializer
        
        return EmpenhoSerializer
   
    ordering_fields = ['valor_total', 'saldo_utilizado', 'codigo']
    ordering = ['-id']  

    
class ItemDoEmpehoViewSet(viewsets.ModelViewSet):
    queryset = ItemEmpenho.objects.all()
    serializer_class = ItemEmpenhoSerializer
    permission_classes = [IsAdmin|IsTecnico]
    pagination_class = None
    
    def get_queryset(self):
        empenho_id = self.request.query_params.get('empenho_id')
        return ItemEmpenho.objects.filter(empenho_id=empenho_id)

class ItemEmpenhoViewSet(viewsets.ModelViewSet):
    queryset = ItemEmpenho.objects.all()
    serializer_class = ItemEmpenhoSerializer
    permission_classes = [IsAdmin|IsTecnico]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return ItemEmpenhoInsertSerializer
        
        return ItemEmpenhoSerializer
    
class OperacaoDoEmpenhoViewSet(viewsets.ModelViewSet):
    queryset = OperacaoItem.objects.all()
    serializer_class = OperacaoItemSerializer
    permission_classes = [IsAdmin|IsTecnico]
    pagination_class = None
    
    def get_queryset(self):
        empenho_id = self.request.query_params.get('empenho_id')
        if empenho_id:
            return OperacaoItem.objects.filter(item_empenho__empenho_id=empenho_id)
        return OperacaoItem.objects.all() 

class OperacaoItemViewSet(viewsets.ModelViewSet):
    queryset = OperacaoItem.objects.all()
    serializer_class = OperacaoItemSerializer
    permission_classes = [IsAdmin|IsTecnico]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return OperacaoItemInsertSerializer
        
        return OperacaoItemSerializer
    
    search_fields = ['tipo', 'item_empenho__item_ata__item_generico__descricao']
    filterset_fields = {
        'tipo': ['exact'], 
        'item_empenho__id': ['exact'],
        'data': ['exact', 'gte', 'lte'],
        'valor': ['exact', 'gte', 'lte'],
    }

    ordering_fields = ['data', 'valor']
    ordering = ['-data']
