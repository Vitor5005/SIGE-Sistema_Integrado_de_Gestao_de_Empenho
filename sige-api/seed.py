"""
Cria um usuário para cada papel do sistema: Diretor, Técnico Administrativo,
Nutricionista e Estoquista.

Uso:  python seed.py

Pode ser executado mais de uma vez: usuários existentes mantêm a senha atual e
apenas têm o papel e o acesso garantidos. Nenhum outro dado é alterado.
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sige_api.settings')

import django

django.setup()

from django.db import transaction

from usuario.models import Usuario
from utils.rbac import Papel


SENHA_PADRAO = 'senha123'

PERFIS = (
    ('diretor', Papel.DIRETOR, 'Diretor', 'SIGE', 'diretor@example.com'),
    ('tecnico', Papel.TECNICO_ADMINISTRATIVO, 'Técnico', 'Administrativo', 'tecnico@example.com'),
    ('nutricionista', Papel.NUTRICIONISTA, 'Nutricionista', 'SIGE', 'nutricionista@example.com'),
    ('estoquista', Papel.ESTOQUISTA, 'Estoquista', 'SIGE', 'estoquista@example.com'),
)


def create_usuarios():
    """Garante os quatro perfis ativos. A senha só é definida na criação."""
    usuarios = {}
    for username, papel, first_name, last_name, email in PERFIS:
        usuario, criado = Usuario.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
            },
        )
        usuario.papel = papel
        usuario.is_active = True
        if papel == Papel.DIRETOR:
            usuario.is_staff = True
            usuario.is_superuser = True
        if criado:
            usuario.set_password(SENHA_PADRAO)
        usuario.save()
        usuarios[papel] = usuario
        print(f"  - {username} ({papel}): {'criado' if criado else 'já existia'}")
    return usuarios


if __name__ == '__main__':
    print('Criando usuários iniciais...')
    with transaction.atomic():
        create_usuarios()
    print('✓ Seed concluído com sucesso!')
