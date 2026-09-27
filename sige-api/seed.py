"""
Cria um usuário para cada papel do sistema: Diretor, Técnico Administrativo,
Nutricionista e Estoquista.

Uso:  python seed.py
      SEED_SENHA='minha-senha' python seed.py   # mesma senha para os quatro

Sem SEED_SENHA, cada usuário novo recebe uma senha aleatória, exibida uma única vez.
Pode ser executado mais de uma vez: usuários existentes mantêm a senha atual e
apenas têm o papel e o acesso garantidos. Nenhum outro dado é alterado.
"""
import os
import secrets

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sige_api.settings')
import django
django.setup()

from usuario.models import Usuario
from utils.rbac import Papel


USUARIOS = (
    {'username': 'diretor', 'first_name': 'Diretor', 'papel': Papel.DIRETOR, 'admin': True},
    {'username': 'tecnico', 'first_name': 'Técnico Administrativo', 'papel': Papel.TECNICO_ADMINISTRATIVO},
    {'username': 'nutricionista', 'first_name': 'Nutricionista', 'papel': Papel.NUTRICIONISTA},
    {'username': 'estoquista', 'first_name': 'Estoquista', 'papel': Papel.ESTOQUISTA},
)


def criar_usuarios_por_papel():
    senha_padrao = os.getenv('SEED_SENHA', '').strip()

    for dados in USUARIOS:
        # O Diretor também acessa o /admin do Django.
        eh_admin = dados.get('admin', False)
        usuario, criado = Usuario.objects.get_or_create(
            username=dados['username'],
            defaults={
                'first_name': dados['first_name'],
                'email': f"{dados['username']}@sige.local",
            },
        )
        usuario.papel = dados['papel']
        usuario.is_active = True
        usuario.is_staff = eh_admin
        usuario.is_superuser = eh_admin

        if criado:
            senha = senha_padrao or secrets.token_urlsafe(9)
            usuario.set_password(senha)
            usuario.save()
            origem = 'SEED_SENHA' if senha_padrao else senha
            print(f"  + {usuario.username:<14} ({usuario.get_papel_display()}) senha: {origem}")
        else:
            usuario.save(update_fields=['papel', 'is_active', 'is_staff', 'is_superuser'])
            print(f"  = {usuario.username:<14} ({usuario.get_papel_display()}) já existia; senha mantida")


if __name__ == '__main__':
    print('Criando usuários por papel...')
    criar_usuarios_por_papel()
    print('Concluído. Troque as senhas após o primeiro acesso.')
