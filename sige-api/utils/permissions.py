from rest_framework.permissions import BasePermission,SAFE_METHODS

from utils.audit import registrar_auditoria, serializar_dados
from utils.rbac import Papel, resolver_acao, tem_permissao


class RBACPermission(BasePermission):
    message = 'Seu papel não possui permissão para executar esta ação.'

    def has_permission(self, request, view):
        recurso = getattr(view, 'rbac_resource', None)
        acao = resolver_acao(view, request)
        usuario = request.user
        papel = getattr(usuario, 'papel', '')

        request._rbac_recurso = recurso
        request._rbac_acao = acao

        permitido = bool(
            usuario
            and usuario.is_authenticated
            and usuario.is_active
            and tem_permissao(papel, recurso, acao)
        )
        if permitido:
            return True

        registrar_auditoria(
            usuario=usuario,
            papel=papel,
            acao=acao or getattr(view, 'action', request.method.lower()),
            recurso=recurso or view.__class__.__name__,
            entidade=view.__class__.__name__,
            entidade_id=getattr(view, 'kwargs', {}).get('pk'),
            valores_novos=serializar_dados(getattr(request, 'data', {})),
            permitido=False,
            detalhe='Tentativa de acesso fora das permissões do papel.',
        )
        return False

class IsAdmin(BasePermission):
    """
    acesso total apenas para usuarios com o pape 'ADMIN'
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.papel == Papel.DIRETOR

class IsTecnico(BasePermission):
    """
    acesso para tecnicos, restringindo a manipulação de usuarios
    """
    def has_permission(self, request, view):
        is_tecnico = request.user and request.user.is_authenticated and request.user.papel == Papel.TECNICO_ADMINISTRATIVO
        if not is_tecnico:
            return False
        if view.__class__.__name__ == 'UsuarioViewSet':
            return False
        return True
