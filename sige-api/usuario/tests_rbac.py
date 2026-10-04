from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from usuario.models import HistoricoAuditoria, Usuario
from utils.rbac import Acao, MATRIZ_PERMISSOES, Papel, Recurso, tem_permissao


class MatrizPermissoesTests(SimpleTestCase):
    def test_matriz_aplica_permissoes_dos_quatro_papeis_em_todos_os_recursos(self):
        papeis = {
            Papel.DIRETOR,
            Papel.TECNICO_ADMINISTRATIVO,
            Papel.NUTRICIONISTA,
            Papel.ESTOQUISTA,
        }

        for recurso, acoes in MATRIZ_PERMISSOES.items():
            for acao, permitidos in acoes.items():
                for papel in papeis:
                    with self.subTest(recurso=recurso, acao=acao, papel=papel):
                        self.assertEqual(
                            tem_permissao(papel, recurso, acao),
                            papel in permitidos,
                        )

    def test_acoes_ausentes_da_matriz_sao_negadas(self):
        for recurso in MATRIZ_PERMISSOES:
            for papel in (Papel.DIRETOR, Papel.TECNICO_ADMINISTRATIVO, Papel.NUTRICIONISTA, Papel.ESTOQUISTA):
                with self.subTest(recurso=recurso, papel=papel):
                    self.assertFalse(tem_permissao(papel, recurso, 'acao_inexistente'))

    def test_regras_centrais_representativas(self):
        casos = (
            (Papel.DIRETOR, Recurso.USUARIO, Acao.CADASTRAR, True),
            (Papel.TECNICO_ADMINISTRATIVO, Recurso.USUARIO, Acao.CADASTRAR, False),
            (Papel.NUTRICIONISTA, Recurso.LICITACAO, Acao.CONSULTAR, True),
            (Papel.NUTRICIONISTA, Recurso.LICITACAO, Acao.EDITAR, False),
            (Papel.DIRETOR, Recurso.ORDEM_ENTREGA, Acao.GERAR_ORDEM, False),
            (Papel.TECNICO_ADMINISTRATIVO, Recurso.ORDEM_ENTREGA, Acao.GERAR_ORDEM, True),
            (Papel.NUTRICIONISTA, Recurso.ITEM_ORDEM, Acao.REGISTRAR_RECEBIMENTO, False),
            (Papel.ESTOQUISTA, Recurso.ESTOQUE, Acao.REGISTRAR_RECEBIMENTO, True),
            (Papel.TECNICO_ADMINISTRATIVO, Recurso.ITEM_ORDEM, Acao.REGISTRAR_RECEBIMENTO, False),
            (Papel.DIRETOR, Recurso.OPERACAO_EMPENHO, Acao.REFORCAR_EMPENHO, True),
            (Papel.NUTRICIONISTA, Recurso.OPERACAO_EMPENHO, Acao.REFORCAR_EMPENHO, False),
            (Papel.NUTRICIONISTA, Recurso.SOLICITACAO_REFORCO, Acao.CADASTRAR, True),
            (Papel.DIRETOR, Recurso.SOLICITACAO_REFORCO, Acao.CADASTRAR, False),
            (Papel.DIRETOR, Recurso.SOLICITACAO_REFORCO, Acao.ALTERAR_STATUS, True),
            (Papel.NUTRICIONISTA, Recurso.SOLICITACAO_REFORCO, Acao.ALTERAR_STATUS, False),
            (Papel.TECNICO_ADMINISTRATIVO, Recurso.OPERACAO_EMPENHO, Acao.REFORCAR_EMPENHO, False),
            (Papel.ESTOQUISTA, Recurso.GENERO_ALIMENTICIO, Acao.CADASTRAR, True),
            (Papel.TECNICO_ADMINISTRATIVO, Recurso.GENERO_ALIMENTICIO, Acao.CADASTRAR, True),
            (Papel.NUTRICIONISTA, Recurso.GENERO_ALIMENTICIO, Acao.CADASTRAR, False),
            (Papel.ESTOQUISTA, Recurso.EMPENHO, Acao.CONSULTAR, False),
            (Papel.ESTOQUISTA, Recurso.PENDENCIA_FORNECEDOR, Acao.ALTERAR_STATUS, False),
            (Papel.TECNICO_ADMINISTRATIVO, Recurso.PENDENCIA_FORNECEDOR, Acao.ALTERAR_STATUS, True),
        )
        for papel, recurso, acao, esperado in casos:
            with self.subTest(papel=papel, recurso=recurso, acao=acao):
                self.assertEqual(tem_permissao(papel, recurso, acao), esperado)


class AuditoriaRBACTests(APITestCase):
    def setUp(self):
        self.diretor = Usuario.objects.create_user(
            username='diretor_rbac',
            password='senha-segura',
            papel=Papel.DIRETOR,
        )
        self.tecnico = Usuario.objects.create_user(
            username='tecnico_rbac',
            password='senha-segura',
            papel=Papel.TECNICO_ADMINISTRATIVO,
        )

    def test_tentativa_negada_retorna_403_e_e_auditada(self):
        self.client.force_authenticate(self.tecnico)

        response = self.client.post(
            reverse('usuario-list'),
            {
                'username': 'usuario_negado',
                'email': 'negado@example.com',
                'first_name': 'Usuário',
                'last_name': 'Negado',
                'papel': Papel.NUTRICIONISTA,
                'password': 'senha-segura',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        evento = HistoricoAuditoria.objects.get(permitido=False)
        self.assertEqual(evento.usuario, self.tecnico)
        self.assertEqual(evento.recurso, Recurso.USUARIO)
        self.assertEqual(evento.acao, Acao.CADASTRAR)
        self.assertEqual(evento.valores_novos['password'], '***')

    def test_escrita_permitida_registra_valores_anteriores_e_novos(self):
        self.client.force_authenticate(self.diretor)

        response = self.client.patch(
            reverse('usuario-detail', args=[self.tecnico.pk]),
            {'is_active': False},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        evento = HistoricoAuditoria.objects.get(permitido=True)
        self.assertTrue(evento.valores_anteriores['is_active'])
        self.assertFalse(evento.valores_novos['is_active'])

    def test_historico_e_somente_leitura(self):
        evento = HistoricoAuditoria.objects.create(
            usuario=self.diretor,
            papel=Papel.DIRETOR,
            acao=Acao.CONSULTAR,
            recurso=Recurso.HISTORICO,
        )

        evento.detalhe = 'alterado'
        with self.assertRaises(ValidationError):
            evento.save()
        with self.assertRaises(ValidationError):
            evento.delete()
        with self.assertRaises(ValidationError):
            HistoricoAuditoria.objects.filter(pk=evento.pk).update(detalhe='alterado')
        with self.assertRaises(ValidationError):
            HistoricoAuditoria.objects.filter(pk=evento.pk).delete()
