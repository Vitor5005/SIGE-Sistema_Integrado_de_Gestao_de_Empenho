from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from usuario.models import Usuario
from utils.rbac import Papel


class UsuarioPermissoesTests(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='admin_teste',
            password='senha-segura',
            papel=Papel.DIRETOR,
        )
        self.tecnico = Usuario.objects.create_user(
            username='tecnico_teste',
            password='senha-segura',
            papel=Papel.TECNICO_ADMINISTRATIVO,
        )

    def dados_novo_usuario(self, username='novo_usuario'):
        return {
            'username': username,
            'email': f'{username}@example.com',
            'first_name': 'Novo',
            'last_name': 'Usuário',
            'papel': Papel.TECNICO_ADMINISTRATIVO,
            'password': 'senha-segura',
        }

    def test_apenas_admin_pode_criar_usuario(self):
        url = reverse('usuario-list')
        self.client.force_authenticate(self.tecnico)

        response = self.client.post(url, self.dados_novo_usuario(), format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Usuario.objects.filter(username='novo_usuario').exists())

        self.client.force_authenticate(self.admin)
        response = self.client.post(url, self.dados_novo_usuario(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_apenas_admin_pode_alterar_status(self):
        url = reverse('usuario-detail', args=[self.tecnico.pk])
        self.client.force_authenticate(self.tecnico)

        response = self.client.patch(url, {'is_active': False}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.tecnico.refresh_from_db()
        self.assertTrue(self.tecnico.is_active)

        self.client.force_authenticate(self.admin)
        response = self.client.patch(url, {'is_active': False}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tecnico.refresh_from_db()
        self.assertFalse(self.tecnico.is_active)

    def test_admin_nao_pode_desativar_a_propria_conta(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            reverse('usuario-detail', args=[self.admin.pk]),
            {'is_active': False},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('is_active', response.data)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_nao_pode_excluir_a_propria_conta(self):
        self.client.force_authenticate(self.admin)

        response = self.client.delete(reverse('usuario-detail', args=[self.admin.pk]))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Usuario.objects.filter(pk=self.admin.pk).exists())

    def test_ultimo_admin_nao_pode_perder_o_papel_de_admin(self):
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            reverse('usuario-detail', args=[self.admin.pk]),
            {'papel': Papel.TECNICO_ADMINISTRATIVO},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('papel', response.data)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.papel, Papel.DIRETOR)
