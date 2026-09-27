from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError

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



class SolicitacaoReforcoTests(APITestCase):
    """Nutricionista pede reforço; Diretor atende (executando o reforço) ou recusa."""

    def setUp(self):
        OperacaoEmpenhoTests.setUp(self)
        registrar_operacao_item(item_empenho_id=self.item.id, tipo='inc', valor='60', data=self.data)
        self.diretor = Usuario.objects.create_user('diretor_ref', password='senha', papel=Papel.DIRETOR)
        self.tecnico = Usuario.objects.create_user('tecnico_ref', password='senha', papel=Papel.TECNICO_ADMINISTRATIVO)
        self.nutricionista = Usuario.objects.create_user('nutri_ref', password='senha', papel=Papel.NUTRICIONISTA)
        self.outra_nutricionista = Usuario.objects.create_user('nutri_ref2', password='senha', papel=Papel.NUTRICIONISTA)
        self.url = reverse('solicitacao-reforco-list')

    def solicitar(self, usuario, quantidade='30', justificativa='Cardápio com carne bovina.'):
        self.client.force_authenticate(usuario)
        return self.client.post(self.url, {
            'item_empenho': self.item.id,
            'quantidade': quantidade,
            'justificativa': justificativa,
        }, format='json')

    def test_nutricionista_solicita_reforco_dentro_do_saldo(self):
        resposta = self.solicitar(self.nutricionista)

        self.assertEqual(resposta.status_code, 201, resposta.data)
        self.assertEqual(resposta.data['status'], SolicitacaoReforco.Status.PENDENTE)
        self.assertEqual(resposta.data['solicitante'], self.nutricionista.id)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, Decimal('60.00'))

    def test_solicitacao_acima_do_saldo_da_arp_e_rejeitada(self):
        resposta = self.solicitar(self.nutricionista, quantidade='41')

        self.assertEqual(resposta.status_code, 400)
        self.assertIn('40.00', str(resposta.data['quantidade']))
        self.assertFalse(SolicitacaoReforco.objects.exists())

    def test_somente_nutricionista_solicita(self):
        for usuario in (self.diretor, self.tecnico):
            self.assertEqual(self.solicitar(usuario).status_code, 403)

    def test_saldo_disponivel_para_o_modal(self):
        self.client.force_authenticate(self.nutricionista)
        resposta = self.client.get(reverse('solicitacao-reforco-saldo'), {'item_empenho': self.item.id})

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['saldo_disponivel'], '40.00')

    def test_diretor_atende_e_o_reforco_e_executado(self):
        solicitacao_id = self.solicitar(self.nutricionista).data['id']

        self.client.force_authenticate(self.diretor)
        resposta = self.client.post(reverse('solicitacao-reforco-atender', args=[solicitacao_id]))

        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.data['status'], SolicitacaoReforco.Status.ATENDIDA)
        self.item.refresh_from_db()
        self.empenho.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, Decimal('90.00'))
        self.assertEqual(self.empenho.valor_total, Decimal('900.00'))
        operacao = SolicitacaoReforco.objects.get(pk=solicitacao_id).operacao
        self.assertEqual((operacao.tipo, operacao.valor), ('ref', Decimal('30.00')))

        self.assertEqual(
            self.client.post(reverse('solicitacao-reforco-atender', args=[solicitacao_id])).status_code, 400,
        )

    def test_atendimento_revalida_o_saldo(self):
        solicitacao_id = self.solicitar(self.nutricionista).data['id']
        registrar_operacao_item(item_empenho_id=self.item.id, tipo='ref', valor='20', data=self.data)

        self.client.force_authenticate(self.diretor)
        resposta = self.client.post(reverse('solicitacao-reforco-atender', args=[solicitacao_id]))

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(SolicitacaoReforco.objects.get(pk=solicitacao_id).status, SolicitacaoReforco.Status.PENDENTE)

    def test_diretor_recusa_com_motivo(self):
        solicitacao_id = self.solicitar(self.nutricionista).data['id']
        url = reverse('solicitacao-reforco-recusar', args=[solicitacao_id])

        self.client.force_authenticate(self.diretor)
        self.assertEqual(self.client.post(url, {'resposta': ' '}, format='json').status_code, 400)
        resposta = self.client.post(url, {'resposta': 'Sem orçamento neste mês.'}, format='json')

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data['status'], SolicitacaoReforco.Status.RECUSADA)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade_atual, Decimal('60.00'))

    def test_nutricionista_nao_atende_e_ve_somente_as_proprias(self):
        solicitacao_id = self.solicitar(self.nutricionista).data['id']
        self.solicitar(self.outra_nutricionista)

        self.client.force_authenticate(self.nutricionista)
        self.assertEqual(
            self.client.post(reverse('solicitacao-reforco-atender', args=[solicitacao_id])).status_code, 403,
        )
        self.assertEqual(self.client.get(self.url).data['count'], 1)

        self.client.force_authenticate(self.diretor)
        self.assertEqual(self.client.get(self.url).data['count'], 2)

        self.client.force_authenticate(self.tecnico)
        self.assertEqual(self.client.get(self.url).status_code, 403)


    def test_resposta_do_diretor_notifica_o_nutricionista_ate_ser_vista(self):
        atendida = self.solicitar(self.nutricionista).data['id']
        recusada = self.solicitar(self.nutricionista, quantidade='5').data['id']
        pendente = self.solicitar(self.nutricionista, quantidade='2').data['id']
        self.client.force_authenticate(self.diretor)
        self.client.post(reverse('solicitacao-reforco-atender', args=[atendida]))
        self.client.post(reverse('solicitacao-reforco-recusar', args=[recusada]), {'resposta': 'Não.'}, format='json')

        self.client.force_authenticate(self.nutricionista)
        nao_vistas = self.client.get(self.url, {'vista_pelo_solicitante': 'false'}).data
        self.assertEqual({item['id'] for item in nao_vistas['results']}, {atendida, recusada})
        self.assertNotIn(pendente, {item['id'] for item in nao_vistas['results']})

        url_vista = reverse('solicitacao-reforco-marcar-vista', args=[atendida])
        self.client.force_authenticate(self.diretor)
        self.assertEqual(self.client.post(url_vista).status_code, 403)

        self.client.force_authenticate(self.nutricionista)
        self.assertTrue(self.client.post(url_vista).data['vista_pelo_solicitante'])
        restantes = self.client.get(self.url, {'vista_pelo_solicitante': 'false'}).data
        self.assertEqual([item['id'] for item in restantes['results']], [recusada])
