from rest_framework import serializers
from usuario.models import Usuario
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
            papel=validated_data.get('papel', 'TECNI')
        )
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['papel'] = user.papel
        token['username'] = user.username 

        return token