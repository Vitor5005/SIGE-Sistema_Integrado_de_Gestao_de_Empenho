from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from cadastro.models import Endereco, Fornecedor, ItemGenerico
from empenho.models import Empenho, ItemEmpenho, OperacaoItem, SolicitacaoReforco
from empenho.services import registrar_operacao_item
from licitacao.models import Ata, ItemAta, Licitacao
from usuario.models import Usuario
from utils.rbac import Papel


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


class SolicitacaoReforcoViewSetTests(APITestCase):
    def setUp(self):
        endereco = Endereco.objects.create(
            lagradouro='Rua A', numero='1', bairro='Centro', cep='69900000',
            municipio='Rio Branco', estado='AC',
        )
        fornecedor = Fornecedor.objects.create(
            razao_social='Fornecedor', nome_fantasia='Fornecedor',
            cnpj='22.222.222/0001-22', endereco=endereco,
        )
        genero = ItemGenerico.objects.create(
            catmat='123456', descricao='Feijão', unidade_medida='KG', categoria='NP',
        )
        licitacao = Licitacao.objects.create(
            numero_licitacao='LIC-REFORCO', validade=12,
            data_abertura='2026-01-01', descricao='Teste de reforço',
        )
        self.ata = Ata.objects.create(
            numero_ata='ATA-REFORCO', ata_saldo_total=Decimal('1000.00'),
            licitacao=licitacao, fornecedor=fornecedor,
        )
        item_ata = ItemAta.objects.create(
            ata=self.ata, item_generico=genero, marca='Marca',
            quantidade_licitada=Decimal('100.00'), valor_unitario=Decimal('10.00'),
        )
        self.empenho = Empenho.objects.create(
            codigo='NE-REFORCO', ata=self.ata, valor_total=Decimal('0.00'),
            saldo_utilizado=Decimal('0.00'),
        )
        self.item = ItemEmpenho.objects.create(
            empenho=self.empenho, item_ata=item_ata,
            quantidade_atual=Decimal('0.00'), quantidade_entrege=Decimal('0.00'),
        )
        self.diretor = Usuario.objects.create_user(
            username='diretor_reforco', password='senha-segura', papel=Papel.DIRETOR,
        )
        self.nutricionista = Usuario.objects.create_user(
            username='nutri_reforco', password='senha-segura', papel=Papel.NUTRICIONISTA,
        )
        self.outra_nutricionista = Usuario.objects.create_user(
            username='outra_nutri_reforco', password='senha-segura', papel=Papel.NUTRICIONISTA,
        )
        self.tecnico = Usuario.objects.create_user(
            username='tecnico_reforco', password='senha-segura',
            papel=Papel.TECNICO_ADMINISTRATIVO,
        )
        self.estoquista = Usuario.objects.create_user(
            username='estoquista_reforco', password='senha-segura', papel=Papel.ESTOQUISTA,
        )
        self.list_url = reverse('solicitacao-reforco-list')
        self.payload = {
            'item_empenho': self.item.pk,
            'quantidade_solicitada': '10.00',
        }

    def criar_solicitacao(self, usuario=None, payload=None):
        self.client.force_authenticate(usuario or self.nutricionista)
        return self.client.post(self.list_url, payload or self.payload, format='json')

    def dados_listagem(self, response):
        return response.data['results'] if isinstance(response.data, dict) else response.data

    def test_nutricionista_cria_solicitacao_valida(self):
        response = self.criar_solicitacao()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_solicitacao_armazena_solicitante_autenticado(self):
        self.criar_solicitacao()

        solicitacao = SolicitacaoReforco.objects.get()
        self.assertEqual(solicitacao.solicitante, self.nutricionista)

    def test_solicitante_enviado_pelo_cliente_e_ignorado(self):
        payload = {**self.payload, 'solicitante': self.outra_nutricionista.pk}
        response = self.criar_solicitacao(payload=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SolicitacaoReforco.objects.get().solicitante, self.nutricionista)

    def test_solicitacao_nao_altera_saldos_ou_operacoes(self):
        quantidade_atual = self.item.quantidade_atual
        valor_total = self.empenho.valor_total
        saldo_ata_total = self.ata.ata_saldo_total
        quantidade_operacoes = OperacaoItem.objects.count()

        response = self.criar_solicitacao()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.item.refresh_from_db()
        self.empenho.refresh_from_db()
        self.ata.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, quantidade_atual)
        self.assertEqual(self.empenho.valor_total, valor_total)
        self.assertEqual(self.ata.ata_saldo_total, saldo_ata_total)
        self.assertEqual(OperacaoItem.objects.count(), quantidade_operacoes)

    def test_quantidade_menor_que_um_e_rejeitada(self):
        response = self.criar_solicitacao(payload={
            **self.payload,
            'quantidade_solicitada': '0.99',
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quantidade_acima_do_saldo_da_arp_e_rejeitada(self):
        response = self.criar_solicitacao(payload={
            **self.payload,
            'quantidade_solicitada': '100.01',
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_solicitacao_aberta_duplicada_para_mesmo_item_e_rejeitada(self):
        self.criar_solicitacao()
        response = self.criar_solicitacao()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            'Já existe uma solicitação de reforço em aberto para este item.',
            str(response.data),
        )

    def test_diretor_nao_pode_criar_solicitacao(self):
        response = self.criar_solicitacao(usuario=self.diretor)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tecnico_nao_pode_criar_solicitacao(self):
        response = self.criar_solicitacao(usuario=self.tecnico)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_estoquista_nao_pode_criar_solicitacao(self):
        response = self.criar_solicitacao(usuario=self.estoquista)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_diretor_lista_todas_as_solicitacoes(self):
        primeira = SolicitacaoReforco.objects.create(
            item_empenho=self.item,
            quantidade_solicitada=Decimal('10.00'),
            solicitante=self.nutricionista,
        )
        segunda = SolicitacaoReforco.objects.create(
            item_empenho=self.item,
            quantidade_solicitada=Decimal('20.00'),
            solicitante=self.outra_nutricionista,
        )
        self.client.force_authenticate(self.diretor)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {dado['id'] for dado in self.dados_listagem(response)},
            {primeira.pk, segunda.pk},
        )

    def test_nutricionista_lista_apenas_suas_solicitacoes(self):
        propria = SolicitacaoReforco.objects.create(
            item_empenho=self.item,
            quantidade_solicitada=Decimal('10.00'),
            solicitante=self.nutricionista,
        )
        SolicitacaoReforco.objects.create(
            item_empenho=self.item,
            quantidade_solicitada=Decimal('20.00'),
            solicitante=self.outra_nutricionista,
        )
        self.client.force_authenticate(self.nutricionista)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [dado['id'] for dado in self.dados_listagem(response)],
            [propria.pk],
        )

    def test_diretor_registra_ciencia(self):
        solicitacao = SolicitacaoReforco.objects.create(
            item_empenho=self.item,
            quantidade_solicitada=Decimal('10.00'),
            solicitante=self.nutricionista,
        )
        self.client.force_authenticate(self.diretor)

        response = self.client.post(
            reverse('solicitacao-reforco-ciente', args=[solicitacao.pk]),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        solicitacao.refresh_from_db()
        self.assertEqual(solicitacao.status, SolicitacaoReforco.Status.CIENTE)
        self.assertEqual(solicitacao.ciente_por, self.diretor)
        self.assertIsNotNone(solicitacao.data_ciencia)

    def test_nutricionista_nao_registra_ciencia(self):
        solicitacao = SolicitacaoReforco.objects.create(
            item_empenho=self.item,
            quantidade_solicitada=Decimal('10.00'),
            solicitante=self.nutricionista,
        )
        self.client.force_authenticate(self.nutricionista)

        response = self.client.post(
            reverse('solicitacao-reforco-ciente', args=[solicitacao.pk]),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nao_permite_registrar_ciencia_duas_vezes(self):
        solicitacao = SolicitacaoReforco.objects.create(
            item_empenho=self.item,
            quantidade_solicitada=Decimal('10.00'),
            solicitante=self.nutricionista,
        )
        self.client.force_authenticate(self.diretor)
        url = reverse('solicitacao-reforco-ciente', args=[solicitacao.pk])

        self.assertEqual(self.client.post(url, format='json').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(url, format='json').status_code, status.HTTP_400_BAD_REQUEST)
