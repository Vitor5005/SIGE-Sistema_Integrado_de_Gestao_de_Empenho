from datetime import date
from unittest import skipUnless

from django.db import IntegrityError, connection, transaction
from django.test import TestCase, TransactionTestCase

from .models import Licitacao


class LicitacaoFactoryMixin:
    def criar_licitacao(self, numero_licitacao, atual=False):
        return Licitacao.objects.create(
            numero_licitacao=numero_licitacao,
            validade=12,
            data_abertura=date(2026, 1, 1),
            atual=atual,
        )


class LicitacaoAtualSaveTests(LicitacaoFactoryMixin, TestCase):
    def test_salvar_nova_licitacao_atual_substitui_a_anterior(self):
        licitacao_a = self.criar_licitacao('LIC-ATUAL-A', atual=True)
        licitacao_b = self.criar_licitacao('LIC-ATUAL-B')

        licitacao_b.atual = True
        licitacao_b.save()

        licitacao_a.refresh_from_db()
        licitacao_b.refresh_from_db()
        self.assertFalse(licitacao_a.atual)
        self.assertTrue(licitacao_b.atual)
        self.assertEqual(Licitacao.objects.filter(atual=True).count(), 1)

    def test_salvar_licitacao_nao_atual_preserva_a_atual(self):
        licitacao_a = self.criar_licitacao('LIC-PRESERVADA-A', atual=True)
        licitacao_b = self.criar_licitacao('LIC-PRESERVADA-B')

        licitacao_b.save()

        licitacao_a.refresh_from_db()
        licitacao_b.refresh_from_db()
        self.assertTrue(licitacao_a.atual)
        self.assertFalse(licitacao_b.atual)
        self.assertEqual(Licitacao.objects.filter(atual=True).count(), 1)


@skipUnless(connection.vendor == 'mysql', 'Requer o indice unico gerado para MySQL.')
class LicitacaoAtualDatabaseConstraintTests(LicitacaoFactoryMixin, TransactionTestCase):
    def test_updates_diretos_nao_permitem_duas_licitacoes_atuais(self):
        licitacao_a = self.criar_licitacao('LIC-INDICE-A')
        licitacao_b = self.criar_licitacao('LIC-INDICE-B')

        Licitacao.objects.filter(pk=licitacao_a.pk).update(atual=True)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Licitacao.objects.filter(pk=licitacao_b.pk).update(atual=True)

        self.assertEqual(Licitacao.objects.filter(atual=True).count(), 1)
        licitacao_a.refresh_from_db()
        self.assertTrue(licitacao_a.atual)
