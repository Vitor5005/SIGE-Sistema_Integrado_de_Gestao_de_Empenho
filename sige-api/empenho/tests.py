from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from cadastro.models import Endereco, Fornecedor, ItemGenerico
from empenho.models import Empenho, ItemEmpenho, OperacaoItem
from empenho.services import registrar_operacao_item
from licitacao.models import Ata, ItemAta, Licitacao


class OperacaoEmpenhoTests(TestCase):
    def setUp(self):
        endereco = Endereco.objects.create(
            lagradouro='Rua A', numero='1', bairro='Centro', cep='69900000',
            municipio='Rio Branco', estado='AC',
        )
        fornecedor = Fornecedor.objects.create(
            razao_social='Fornecedor', nome_fantasia='Fornecedor',
            cnpj='11.111.111/0001-11', endereco=endereco,
        )
        genero = ItemGenerico.objects.create(
            catmat='987654', descricao='Arroz', unidade_medida='KG', categoria='NP',
        )
        licitacao = Licitacao.objects.create(
            numero_licitacao='ARP-TESTE', validade=12,
            data_abertura='2026-01-01', descricao='Teste',
        )
        self.ata = Ata.objects.create(
            numero_ata='ATA-TESTE', ata_saldo_total=Decimal('1000.00'),
            licitacao=licitacao, fornecedor=fornecedor,
        )
        self.item_ata = ItemAta.objects.create(
            ata=self.ata, item_generico=genero, marca='Marca',
            quantidade_licitada=Decimal('100.00'), valor_unitario=Decimal('10.00'),
        )
        self.empenho = Empenho.objects.create(
            codigo='NE-TESTE', ata=self.ata, valor_total=Decimal('0.00'),
            saldo_utilizado=Decimal('0.00'),
        )
        self.item = ItemEmpenho.objects.create(
            empenho=self.empenho, item_ata=self.item_ata,
            quantidade_atual=Decimal('0.00'), quantidade_entrege=Decimal('0.00'),
        )
        self.data = datetime(2026, 1, 1, tzinfo=dt_timezone.utc)

    def operar(self, tipo, valor):
        return registrar_operacao_item(
            item_empenho_id=self.item.id, tipo=tipo, valor=valor, data=self.data,
        )

    def test_inclusao_reforco_e_anulacao_atualizam_saldos(self):
        self.operar('inc', '10')
        self.operar('ref', '20')
        self.operar('anl', '5')
        self.item.refresh_from_db()
        self.empenho.refresh_from_db()
        self.ata.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, Decimal('25.00'))
        self.assertEqual(self.empenho.valor_total, Decimal('250.00'))
        self.assertEqual(self.ata.ata_saldo_total, Decimal('750.00'))

    def test_operacao_que_excede_arp_e_rejeitada_sem_alteracao(self):
        self.operar('inc', '100')
        with self.assertRaises(ValidationError):
            self.operar('ref', '1')
        self.assertEqual(OperacaoItem.objects.count(), 1)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, Decimal('100.00'))

    def test_anulacao_nao_pode_consumir_quantidade_reservada_em_ordem(self):
        self.operar('inc', '10')
        self.item.quantidade_atual = Decimal('4.00')
        self.item.save(update_fields=['quantidade_atual'])
        with self.assertRaises(ValidationError):
            self.operar('anl', '5')

    def test_quantidade_minima_e_um(self):
        with self.assertRaises(ValidationError):
            self.operar('inc', '0.99')
        self.assertFalse(OperacaoItem.objects.exists())
