from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from cardapio import services
from cardapio.models import Cardapio
from cardapio.serializers import (
    CardapioResumoSerializer,
    CardapioSerializer,
    MotivoSerializer,
    QuantidadesItensSerializer,
)
from utils.mixins import AuditoriaRBACMixin, BaseFiltroMixin
from utils.rbac import Acao, Recurso


class CardapioViewSet(AuditoriaRBACMixin, BaseFiltroMixin, viewsets.ModelViewSet):
    queryset = Cardapio.objects.select_related(
        'criado_por', 'aprovado_por', 'finalizado_por',
    ).prefetch_related('itens__item_generico')
    serializer_class = CardapioSerializer
    rbac_resource = Recurso.CARDAPIO
    rbac_action_map = {
        'disponibilidade': Acao.CONSULTAR,
        'enviar': Acao.EDITAR,
        'informar_consumo': Acao.EDITAR,
        'aprovar': Acao.APROVAR,
        'recusar': Acao.APROVAR,
        'confirmar_consumo': Acao.APROVAR,
        'devolver_consumo': Acao.APROVAR,
    }
    search_fields = ['preparacoes', 'itens__item_generico__descricao']
    filterset_fields = {
        'status': ['exact', 'in'],
        'refeicao': ['exact'],
        'data': ['exact', 'gte', 'lte'],
    }
    ordering_fields = ['data', 'refeicao', 'status', 'atualizado_em']
    ordering = ['-data', '-id']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            return queryset.annotate(total_itens=Count('itens', distinct=True))
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return CardapioResumoSerializer
        return CardapioSerializer

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)

    def destroy(self, request, *args, **kwargs):
        cardapio = self.get_object()
        if not cardapio.editavel:
            raise ValidationError({'status': 'Somente rascunhos ou cardápios recusados podem ser excluídos.'})
        return super().destroy(request, *args, **kwargs)

    def _responder(self, cardapio):
        cardapio = self.get_queryset().get(pk=cardapio.pk)
        return Response(CardapioSerializer(cardapio, context=self.get_serializer_context()).data)

    @action(detail=False, methods=['get'])
    def disponibilidade(self, request):
        """Saldo disponível por gênero, descontando cardápios enviados (exceto o informado em ?cardapio=)."""
        excluir = request.query_params.get('cardapio')
        excluir = int(excluir) if excluir and excluir.isdigit() else None
        return Response(services.disponibilidade(excluir_cardapio_id=excluir))

    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        cardapio = services.enviar(cardapio_id=self.get_object().pk, usuario=request.user)
        return self._responder(cardapio)

    @action(detail=True, methods=['post'])
    def recusar(self, request, pk=None):
        dados = MotivoSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        cardapio = services.recusar(
            cardapio_id=self.get_object().pk, motivo=dados.validated_data['motivo'], usuario=request.user,
        )
        return self._responder(cardapio)

    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        dados = QuantidadesItensSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        cardapio = services.aprovar(
            cardapio_id=self.get_object().pk, quantidades=dados.validated_data['itens'], usuario=request.user,
        )
        return self._responder(cardapio)

    @action(detail=True, methods=['post'], url_path='informar-consumo')
    def informar_consumo(self, request, pk=None):
        dados = QuantidadesItensSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        cardapio = services.informar_consumo(
            cardapio_id=self.get_object().pk, quantidades=dados.validated_data['itens'], usuario=request.user,
        )
        return self._responder(cardapio)

    @action(detail=True, methods=['post'], url_path='devolver-consumo')
    def devolver_consumo(self, request, pk=None):
        dados = MotivoSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        cardapio = services.devolver_consumo(
            cardapio_id=self.get_object().pk, motivo=dados.validated_data['motivo'], usuario=request.user,
        )
        return self._responder(cardapio)

    @action(detail=True, methods=['post'], url_path='confirmar-consumo')
    def confirmar_consumo(self, request, pk=None):
        cardapio = services.confirmar_consumo(cardapio_id=self.get_object().pk, usuario=request.user)
        return Response(
            CardapioSerializer(
                self.get_queryset().get(pk=cardapio.pk), context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_200_OK,
        )
