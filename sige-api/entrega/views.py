import yagmail
import tempfile
import os
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser,FormParser
from rest_framework import viewsets

from entrega.models import OrdemEntrega, ItemOrdem
from entrega.serializers import OrdemEntregaInsertSerializer, OrdemEntregaSerializer, ItemOrdemSerializer, itemOrdemInsertSerializer
from licitacao.views import BaseFiltroMixin
from utils.permissions import IsAdmin, IsTecnico

class EntregaViewSet(BaseFiltroMixin,viewsets.ModelViewSet):
    queryset = OrdemEntrega.objects.all()
    serializer_class = OrdemEntregaSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    permission_classes = [IsAdmin|IsTecnico]

    def get_serializer_class(self):
        
        if self.action in ['create', 'update']:
            return OrdemEntregaInsertSerializer
        
        return OrdemEntregaSerializer
    
    search_fields = ['codigo', 'empenho__codigo']
    filterset_fields = {
        'status': ['exact'],                         
        'empenho__id': ['exact'],                    
        'data_emissao': ['exact', 'gte', 'lte'],     
        'data_entrega': ['exact', 'gte', 'lte', 'isnull'],  
        'valor_total_executado': ['exact', 'gte', 'lte']
    }

    ordering_fields = ['data_emissao', 'data_entrega', 'valor_total_executado']
    ordering = ['-data_emissao']
    
    @action(
        detail=True,
        methods=['post'],
        url_path='enviar-pedido',
        parser_classes=[JSONParser, MultiPartParser, FormParser]
    )
    def EnviarPedidoPorEmail(self, request, pk=None):
        """
        Envia um e-mail com um Pedido de Entrega em anexo 
        para o fornecedor associado a esta Ordem de Entrega.
        """
        try:
            ordem_de_entrega = self.get_object()
            fornecedor = ordem_de_entrega.empenho.ata.fornecedor
        except OrdemEntrega.DoesNotExist:
            return Response({'erro': 'Ordem de Entrega não encontrada'},status=status.HTTP_404_NOT_FOUND)
        except AttributeError:
            return Response({'erro': 'Não foi possível encontrar o fornecedor associado a esta ordem de entrega.'},status=status.HTTP_404_NOT_FOUND)
        
        if not fornecedor.email:
            return Response({'erro': f'O fornecedor "{fornecedor.nome_fantasia}" não possui um e-mail cadastrado.'}, status=status.HTTP_400_BAD_REQUEST)
        assunto = request.data.get('assunto', f'Pedido de Entrega: {ordem_de_entrega.codigo}')
        mensagem_requisicao = (
            request.data.get('corpo_mensagem')
            or request.data.get('mensagem')
            or request.data.get('mensagem_solicitacao')
        )
        corpo_mensagem = mensagem_requisicao if mensagem_requisicao else (
            f'Prezado Fornecedor {fornecedor.nome_fantasia},\n\n'
            f'Segue em anexo o pedido de entrega referente à ordem {ordem_de_entrega.codigo}.\n\n'
            f'Atenciosamente,\nEquipe SIGE.'
        )
        anexo = request.FILES.get('anexo')

        if not anexo:
            return Response({'erro': 'Nenhum arquivo foi enviado. O campo deve se chamar "anexo".'}, status=status.HTTP_400_BAD_REQUEST)
        caminho_temporario_anexo = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{anexo.name}") as temp_file:
                for chunk in anexo.chunks():
                    temp_file.write(chunk)
                caminho_temporario_anexo = temp_file.name
            email_usuario = "rusige6@gmail.com"
            senha_usuario = "ocpc ptcw bwuw jixg"
            servidor_email = yagmail.SMTP(user=email_usuario, password=senha_usuario) 
            #conteudo_anexo = {anexo.name: anexo.read()}
            servidor_email.send(
                to=fornecedor.email,
                subject=assunto,
                contents=corpo_mensagem,
                attachments=caminho_temporario_anexo
            )
        except Exception as erro:
            print(f"ERRO AO ENVIAR E-MAIL DO PEDIDO: {erro}")
            return Response({'erro': 'Ocorreu um problema interno ao tentar enviar o e-mail.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if caminho_temporario_anexo and os.path.exists(caminho_temporario_anexo):
                os.remove(caminho_temporario_anexo)
                
        return Response({'sucesso': f'Pedido de entrega enviado com sucesso para {fornecedor.email}.'}, status=status.HTTP_200_OK)

    
class PedidosDaOrdemViewSet(viewsets.ModelViewSet):
    queryset = ItemOrdem.objects.all()
    serializer_class = ItemOrdemSerializer
    permission_classes = [IsAdmin|IsTecnico]
    
    def get_queryset(self):
            queryset = super().get_queryset()
            ordem_id = self.request.query_params.get('ordem_id')
            if ordem_id is not None:
                queryset = queryset.filter(ordem_entrega__id=ordem_id)
            return queryset
    
class ItemEntregaViewSet(viewsets.ModelViewSet):
    queryset = ItemOrdem.objects.all()
    serializer_class = ItemOrdemSerializer
    permission_classes = [IsAdmin|IsTecnico]

    def get_serializer_class(self):
        
        if self.action in ['create', 'update']:
            return itemOrdemInsertSerializer
        
        return itemOrdemInsertSerializer
    
    search_fields = ['observacao', 'ordem_entrega__codigo', 'item_empenho__item_ata__item_generico__descricao']

    filterset_fields = {
        'ordem_entrega__id': ['exact'],
        'item_empenho__id': ['exact'],
        'quantidade_solicitada': ['exact', 'gte', 'lte'],
        'quantidade_entregue': ['exact', 'gte', 'lte']
    }

    ordering_fields = ['quantidade_solicitada', 'quantidade_entregue']
    ordering = ['id']