from rest_framework import viewsets
from usuario.models import Usuario
from usuario.serializers import UsuarioSerializer
from licitacao.views import BaseFiltroMixin 
from rest_framework_simplejwt.views import TokenObtainPairView
from usuario.serializers import CustomTokenObtainPairSerializer

class UsuarioViewSet(BaseFiltroMixin, viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    
    search_fields = ['username', 'first_name', 'last_name', 'email']
    filterset_fields = {
        'papel': ['exact'],
        'is_active': ['exact'],
    }
    
    ordering_fields = ['username', 'first_name', 'date_joined']
    ordering = ['username']
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer