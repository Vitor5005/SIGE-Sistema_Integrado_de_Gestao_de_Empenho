from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from utils.audit import registrar_auditoria, serializar_dados, serializar_instancia
from utils.permissions import RBACPermission


class RBACMixin:
    """Aplica a matriz de permissões por papel (utils.rbac) à view."""
    permission_classes = [RBACPermission]


class AuditoriaRBACMixin(RBACMixin):
    """Aplica o RBAC e registra no histórico de auditoria toda escrita bem-sucedida."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._auditoria_anterior = {}
        self._auditoria_instancia_id = kwargs.get(
            getattr(self, 'lookup_url_kwarg', None) or getattr(self, 'lookup_field', 'pk')
        )

        if request.method in {'PUT', 'PATCH', 'DELETE', 'POST'} and self._auditoria_instancia_id:
            queryset = self.get_queryset()
            instancia = queryset.model._default_manager.filter(
                pk=self._auditoria_instancia_id
            ).first()
            self._auditoria_anterior = serializar_instancia(instancia)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        acao = getattr(request, '_rbac_acao', None)
        recurso = getattr(request, '_rbac_recurso', None)
        if (
            request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}
            or response.status_code >= 400
            or not acao
            or not recurso
        ):
            return response

        queryset = self.get_queryset()
        model = queryset.model
        entidade_id = self._auditoria_instancia_id
        if entidade_id is None and isinstance(getattr(response, 'data', None), dict):
            entidade_id = response.data.get('id')

        instancia_nova = None
        if request.method != 'DELETE' and entidade_id is not None:
            instancia_nova = model._default_manager.filter(pk=entidade_id).first()

        registrar_auditoria(
            usuario=request.user,
            papel=getattr(request.user, 'papel', ''),
            acao=acao,
            recurso=recurso,
            entidade=model._meta.label,
            entidade_id=entidade_id,
            valores_anteriores=getattr(self, '_auditoria_anterior', {}),
            valores_novos=(
                serializar_instancia(instancia_nova)
                if instancia_nova is not None
                else serializar_dados(getattr(request, 'data', {}))
            ),
            permitido=True,
        )
        return response


class BaseFiltroMixin:
    """
    Mixin de configuração padrão de busca, filtro e ordenação
    a qualquer ModelViewSet que precisar.
    """
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]


class SerializerEscritaMixin:
    """
    Usa `serializer_class_escrita` (campos planos, com ids) no create/update
    e `serializer_class` (aninhado) nas leituras.
    """
    serializer_class_escrita = None
    acoes_escrita = ('create', 'update')

    def get_serializer_class(self):
        if self.serializer_class_escrita and self.action in self.acoes_escrita:
            return self.serializer_class_escrita
        return super().get_serializer_class()


class FiltroQueryParamMixin:
    """
    Filtra o queryset por parâmetros da URL: `filtros_query_param` mapeia
    parâmetro -> lookup do ORM. Com `filtros_obrigatorios`, a ausência de
    qualquer parâmetro retorna uma lista vazia em vez de todos os registros.
    """
    filtros_query_param = {}
    filtros_obrigatorios = False

    def get_queryset(self):
        queryset = super().get_queryset()
        for parametro, lookup in self.filtros_query_param.items():
            valor = self.request.query_params.get(parametro)
            if valor:
                queryset = queryset.filter(**{lookup: valor})
            elif self.filtros_obrigatorios:
                return queryset.none()
        return queryset


class EscopoPorPapelMixin:
    """
    Restringe o queryset conforme o papel do usuário: `escopo_por_papel`
    mapeia papel -> função (usuario) que devolve o Q do que ele pode ver.
    Papéis ausentes do mapa veem todos os registros.
    """
    escopo_por_papel = {}

    def get_queryset(self):
        queryset = super().get_queryset()
        usuario = self.request.user
        escopo = self.escopo_por_papel.get(getattr(usuario, 'papel', None))
        return queryset.filter(escopo(usuario)) if escopo else queryset
