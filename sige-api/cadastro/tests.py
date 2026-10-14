import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from cadastro.models import ItemGenerico
from estoque.models import Estoque
from usuario.models import Usuario
from utils.rbac import Papel

MEDIA_TESTE = tempfile.mkdtemp()


def imagem_png(nome='banana.png'):
    conteudo = io.BytesIO()
    Image.new('RGB', (8, 8), color='yellow').save(conteudo, format='PNG')
    return SimpleUploadedFile(nome, conteudo.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=MEDIA_TESTE)
class ImagemItemGenericoTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TESTE, ignore_errors=True)

    def setUp(self):
        self.estoquista = Usuario.objects.create_user(
            username='estoquista_imagem', password='senha-segura', papel=Papel.ESTOQUISTA,
        )
        self.nutricionista = Usuario.objects.create_user(
            username='nutricionista_imagem', password='senha-segura', papel=Papel.NUTRICIONISTA,
        )
        self.item = ItemGenerico.objects.create(
            catmat='400001', descricao='Banana Prata', unidade_medida='KG', categoria='Fr',
        )
        self.url = reverse('itemgenerico-imagem', args=[self.item.pk])

    def test_envia_imagem_e_a_exibe_no_genero_e_no_estoque(self):
        Estoque.objects.get_or_create(item_generico=self.item)
        self.client.force_authenticate(self.estoquista)

        response = self.client.post(self.url, {'imagem': imagem_png()}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('/media/generos/', response.data['imagem'])

        estoque = self.client.get(reverse('estoque-list'))
        self.assertIn('/media/generos/', estoque.data['results'][0]['imagem'])

    def test_substituir_e_remover_apagam_o_arquivo_anterior(self):
        self.client.force_authenticate(self.estoquista)
        self.client.post(self.url, {'imagem': imagem_png('primeira.png')}, format='multipart')
        self.item.refresh_from_db()
        primeira = self.item.imagem.name

        self.client.post(self.url, {'imagem': imagem_png('segunda.png')}, format='multipart')
        self.item.refresh_from_db()
        self.assertFalse(self.item.imagem.storage.exists(primeira))

        segunda = self.item.imagem.name
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.item.refresh_from_db()
        self.assertFalse(self.item.imagem)
        self.assertFalse(self.item.imagem.storage.exists(segunda))

    def test_rejeita_arquivo_que_nao_e_imagem(self):
        self.client.force_authenticate(self.estoquista)
        arquivo = SimpleUploadedFile('falso.png', b'nao sou uma imagem', content_type='image/png')

        response = self.client.post(self.url, {'imagem': arquivo}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_papel_sem_permissao_de_edicao_nao_envia_imagem(self):
        self.client.force_authenticate(self.nutricionista)

        response = self.client.post(self.url, {'imagem': imagem_png()}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_genero_sem_imagem_continua_editavel(self):
        self.client.force_authenticate(self.estoquista)

        response = self.client.patch(
            reverse('itemgenerico-detail', args=[self.item.pk]),
            {'descricao': 'Banana Nanica'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['imagem'])
