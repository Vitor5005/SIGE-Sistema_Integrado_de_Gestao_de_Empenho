from rest_framework.permissions import BasePermission,SAFE_METHODS

class IsAdmin(BasePermission):
    """
    acesso total apenas para usuarios com o pape 'ADMIN'
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.papel == 'ADMIN'

class IsTecnico(BasePermission):
    """
    acesso para tecnicos, restringindo a manipulação de usuarios
    """
    def has_permission(self, request, view):
        is_tecnico = request.user and request.user.is_authenticated and request.user.papel == 'TECNI'
        if not is_tecnico:
            return False
        if view.__class__.__name__ == 'UsuarioViewSet':
            return False
        return True