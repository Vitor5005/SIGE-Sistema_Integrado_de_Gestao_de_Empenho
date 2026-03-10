# sige-api/usuario/views.py

import random
import yagmail
from django.utils import timezone
from django.core.signing import  TimestampSigner, BadSignature, SignatureExpired 
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from usuario.models import Usuario, CodigoRedefiniçãoSenha 
from usuario.serializers import UsuarioSerializer, CustomTokenObtainPairSerializer
from licitacao.views import BaseFiltroMixin

signer = TimestampSigner()

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

    @action(detail=False, methods=['post'], url_path='request-password-reset', permission_classes=[AllowAny])
    def request_password_reset(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'O e-mail é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
           
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            
            return Response({'success': 'Se um usuário com este e-mail existir, um código foi enviado.'}, status=status.HTTP_200_OK)

        code_value = str(random.randint(100000, 999999))
        
        CodigoRedefiniçãoSenha.objects.filter(usuario=user).delete()
        CodigoRedefiniçãoSenha.objects.create(usuario=user, codigo=code_value)

        try:
            email_user = "rusige6@gmail.com"
            email_password = "ocpc ptcw bwuw jixg"
            yag = yagmail.SMTP(user=email_user, password=email_password)
            yag.send(
                to=user.email,
                subject='Código de Redefinição de Senha',
                contents=f'Olá, seu código para redefinir a senha é: {code_value}. \nEste código expira em 10 minutos.'
            )
        except Exception as e:
            print(f"ERRO AO ENVIAR E-MAIL DE REDEFINIÇÃO: {e}")
            return Response({'error': 'Ocorreu um problema ao enviar o e-mail.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'success': 'Se um usuário com este e-mail existir, um código foi enviado.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='verify-reset-code', permission_classes=[AllowAny])
    def verify_reset_code(self, request):
        code_value = request.data.get('code')
        if not code_value:
            return Response({'error': 'O código é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            reset_instance = CodigoRedefiniçãoSenha.objects.get(codigo=code_value)
        except CodigoRedefiniçãoSenha.DoesNotExist:
            return Response({'error': 'Código inválido.'}, status=status.HTTP_400_BAD_REQUEST)

   
        if timezone.now() > reset_instance.expira_em:
            reset_instance.delete()
            return Response({'error': 'O código de redefinição expirou.'}, status=status.HTTP_400_BAD_REQUEST)
        
        
        reset_token = signer.sign(str(reset_instance.usuario.pk))
        reset_instance.delete()

        return Response({
            'success': 'Código verificado com sucesso.',
            'reset_token': reset_token
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='set-new-password', permission_classes=[AllowAny])
    def set_new_password(self, request):
        token = request.data.get('reset_token')
        new_password = request.data.get('password')

        if not all([token, new_password]):
            return Response({'error': 'Token de redefinição e nova senha são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
           
            user_pk = signer.unsign(token, max_age=300)
           
            user = Usuario.objects.get(pk=user_pk)
        except SignatureExpired:
            return Response({'error': 'O token de redefinição expirou. Por favor, solicite um novo código.'}, status=status.HTTP_400_BAD_REQUEST)
        except (BadSignature, Usuario.DoesNotExist):
            return Response({'error': 'Token de redefinição inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({'success': 'Senha atualizada com sucesso.'}, status=status.HTTP_200_OK)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer