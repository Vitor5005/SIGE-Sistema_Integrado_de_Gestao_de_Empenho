import tempfile
import os
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser,FormParser
from rest_framework import viewsets

from django.db.models import Q
from django.utils import timezone

from entrega.models import OrdemEntrega, ItemOrdem, PendenciaFornecedor
from entrega.serializers import OrdemEntregaInsertSerializer, OrdemEntregaSerializer, ItemOrdemSerializer, itemOrdemInsertSerializer, PendenciaFornecedorSerializer
from utils.mail import get_email_client
from utils.mixins import (
    AuditoriaRBACMixin,
    BaseFiltroMixin,
    EscopoPorPapelMixin,
    FiltroQueryParamMixin,
    SerializerEscritaMixin,
)
from utils.rbac import Acao, Papel, Recurso

class EntregaViewSet(AuditoriaRBACMixin, BaseFiltroMixin, SerializerEscritaMixin, viewsets.ModelViewSet):
    queryset = OrdemEntrega.objects.all()
    serializer_class = OrdemEntregaSerializer
    serializer_class_escrita = OrdemEntregaInsertSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    rbac_resource = Recurso.ORDEM_ENTREGA
    rbac_action_map = {'EnviarPedidoPorEmail': Acao.EMITIR_ORDEM}

    def perform_create(self, serializer):
        serializer.save(solicitante=self.request.user)

    search_fields = ['codigo', 'empenho__codigo']
    filterset_fields = {
        'status': ['exact'],
        'empenho__id': ['exact'],
        'empenho__ata__licitacao__id': ['exact'],
        'data_emissao': ['exact', 'gte', 'lte'],
        'data_entrega_prevista': ['exact', 'gte', 'lte'],
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
            servidor_email = get_email_client()
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


class PedidosDaOrdemViewSet(AuditoriaRBACMixin, FiltroQueryParamMixin, viewsets.ModelViewSet):
    queryset = ItemOrdem.objects.all()
    serializer_class = ItemOrdemSerializer
    pagination_class = None
    rbac_resource = Recurso.ITEM_ORDEM
    filtros_query_param = {'ordem_id': 'ordem_entrega__id'}

class ItemEntregaViewSet(AuditoriaRBACMixin, BaseFiltroMixin, viewsets.ModelViewSet):
    queryset = ItemOrdem.objects.all()
    serializer_class = itemOrdemInsertSerializer
    rbac_resource = Recurso.ITEM_ORDEM

    search_fields = ['observacao', 'ordem_entrega__codigo', 'item_empenho__item_ata__item_generico__descricao']

    filterset_fields = {
        'ordem_entrega__id': ['exact'],
        'item_empenho__id': ['exact'],
        'quantidade_solicitada': ['exact', 'gte', 'lte'],
        'quantidade_entregue': ['exact', 'gte', 'lte']
    }

    ordering_fields = ['quantidade_solicitada', 'quantidade_entregue']
    ordering = ['id']


class PendenciaFornecedorViewSet(
    AuditoriaRBACMixin, BaseFiltroMixin, EscopoPorPapelMixin, viewsets.ReadOnlyModelViewSet
):
    """
    Pendências de fornecedores geradas em recebimentos parciais.
    O Técnico vê as pendências das ordens que solicitou (ou sem solicitante
    identificado); Diretor e Estoquista veem todas.
    """
    queryset = PendenciaFornecedor.objects.select_related(
        'item_ordem__ordem_entrega__empenho__ata__fornecedor',
        'item_ordem__item_empenho__item_ata__item_generico',
        'registrada_por', 'destinatario', 'ciente_por',
    )
    serializer_class = PendenciaFornecedorSerializer
    rbac_resource = Recurso.PENDENCIA_FORNECEDOR
    rbac_action_map = {'ciente': Acao.ALTERAR_STATUS}
    escopo_por_papel = {
        Papel.TECNICO_ADMINISTRATIVO: lambda usuario: Q(destinatario=usuario) | Q(destinatario__isnull=True),
    }

    filterset_fields = {
        'status': ['exact', 'in'],
        'item_ordem__ordem_entrega__id': ['exact'],
    }
    search_fields = [
        'item_ordem__ordem_entrega__codigo',
        'item_ordem__ordem_entrega__empenho__ata__fornecedor__nome_fantasia',
        'item_ordem__item_empenho__item_ata__item_generico__descricao',
    ]
    ordering_fields = ['data_registro', 'data_atualizacao', 'quantidade_pendente']
    ordering = ['-data_atualizacao', '-id']

    @action(detail=True, methods=['post'])
    def ciente(self, request, pk=None):
        pendencia = self.get_object()
        if pendencia.status != PendenciaFornecedor.Status.ABERTA:
            return Response(
                {'status': 'Somente pendências abertas podem ser marcadas como cientes.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pendencia.status = PendenciaFornecedor.Status.CIENTE
        pendencia.ciente_por = request.user
        pendencia.data_ciencia = timezone.now()
        pendencia.save(update_fields=['status', 'ciente_por', 'data_ciencia', 'data_atualizacao'])
        return Response(self.get_serializer(pendencia).data)
