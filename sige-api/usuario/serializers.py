from rest_framework import serializers
from usuario.models import HistoricoAuditoria, Usuario
from utils.rbac import Papel
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'papel', 'is_active', 'password')
        extra_kwargs = {
            'password': {'write_only': True, 'required': True}
        }

    def create(self, validated_data):
       
        usuario = Usuario.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],
            papel=validated_data.get('papel', Papel.TECNICO_ADMINISTRATIVO)
        )
        return usuario

    def validate(self, attrs):
        request = self.context.get('request')
        usuario_logado = getattr(request, 'user', None)

        if self.instance and usuario_logado and usuario_logado.is_authenticated:
            if self.instance.pk == usuario_logado.pk and attrs.get('is_active') is False:
                raise serializers.ValidationError({
                    'is_active': 'Você não pode desativar a própria conta.'
                })

            novo_papel = attrs.get('papel', self.instance.papel)
            if (
                self.instance.papel == Papel.DIRETOR
                and novo_papel != Papel.DIRETOR
                and not Usuario.objects.filter(
                    papel=Papel.DIRETOR,
                    is_active=True,
                ).exclude(pk=self.instance.pk).exists()
            ):
                raise serializers.ValidationError({
                    'papel': 'O sistema deve manter pelo menos um administrador ativo.'
                })

        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance


class HistoricoAuditoriaSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = HistoricoAuditoria
        fields = (
            'id', 'usuario', 'usuario_username', 'papel', 'acao', 'recurso',
            'entidade', 'entidade_id', 'valores_anteriores', 'valores_novos',
            'permitido', 'detalhe', 'data_hora',
        )
        read_only_fields = fields


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['papel'] = user.papel
        token['username'] = user.username 

        return token
