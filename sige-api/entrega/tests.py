from datetime import datetime, timezone as dt_timezone
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from entrega.models import OrdemEntrega, PendenciaFornecedor
from utils.estoque_services import registrar_recebimento
from estoque.tests import EstoqueBaseMixin
from usuario.models import HistoricoAuditoria, Usuario
from utils.rbac import Acao, Papel, Recurso


class PendenciaFornecedorTests(EstoqueBaseMixin, APITestCase):
    def setUp(self):
        self.criar_cenario()
        self.ordem.solicitante = self.tecnico
        self.ordem.save(update_fields=['solicitante'])

    def receber(self, quantidade, observacao=''):
        return registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'quantidade_recebida': quantidade,
                'observacao': observacao,
            }],
            usuario=self.estoquista,
        )

    def test_recebimento_parcial_gera_pendencia_para_o_solicitante(self):
        self.receber('100', '400 kg impróprios para consumo.')

        pendencia = PendenciaFornecedor.objects.get()
        self.assertEqual(pendencia.status, PendenciaFornecedor.Status.ABERTA)
        self.assertEqual(pendencia.quantidade_pendente, Decimal('400.000'))
        self.assertEqual(pendencia.motivo, '400 kg impróprios para consumo.')
        self.assertEqual(pendencia.destinatario, self.tecnico)
        self.assertEqual(pendencia.registrada_por, self.estoquista)

    def test_recebimento_completo_nao_gera_pendencia(self):
        self.receber('500')
        self.assertFalse(PendenciaFornecedor.objects.exists())

    def test_novo_recebimento_parcial_atualiza_e_reabre_a_mesma_pendencia(self):
        self.receber('100', 'Faltaram 400 kg.')
        pendencia = PendenciaFornecedor.objects.get()
        pendencia.status = PendenciaFornecedor.Status.CIENTE
        pendencia.save()

        self.receber('300', 'Ainda faltam 100 kg.')

        pendencia.refresh_from_db()
        self.assertEqual(PendenciaFornecedor.objects.count(), 1)
        self.assertEqual(pendencia.status, PendenciaFornecedor.Status.ABERTA)
        self.assertEqual(pendencia.quantidade_pendente, Decimal('100.000'))
        self.assertEqual(pendencia.motivo, 'Ainda faltam 100 kg.')

    def test_entrega_do_restante_resolve_a_pendencia(self):
        self.receber('100', 'Faltaram 400 kg.')
        self.receber('400')

        pendencia = PendenciaFornecedor.objects.get()
        self.assertEqual(pendencia.status, PendenciaFornecedor.Status.RESOLVIDA)
        self.assertEqual(pendencia.quantidade_pendente, Decimal('0.000'))
        self.assertIsNotNone(pendencia.data_resolucao)

    def test_ordem_antiga_usa_o_historico_para_identificar_o_solicitante(self):
        self.ordem.solicitante = None
        self.ordem.save(update_fields=['solicitante'])
        HistoricoAuditoria.objects.create(
            usuario=self.tecnico,
            papel=Papel.TECNICO_ADMINISTRATIVO,
            acao=Acao.GERAR_ORDEM,
            recurso=Recurso.ORDEM_ENTREGA,
            entidade='entrega.OrdemEntrega',
            entidade_id=str(self.ordem.id),
        )

        self.receber('100', 'Faltaram 400 kg.')

        self.assertEqual(PendenciaFornecedor.objects.get().destinatario, self.tecnico)

    def test_tecnico_ve_somente_pendencias_das_suas_ordens(self):
        self.receber('100', 'Faltaram 400 kg.')
        outro_tecnico = Usuario.objects.create_user(
            'outro_tecnico', password='senha', papel=Papel.TECNICO_ADMINISTRATIVO,
        )
        url = reverse('pendencia-fornecedor-list')

        for usuario, esperado in ((self.tecnico, 1), (outro_tecnico, 0), (self.diretor, 1), (self.estoquista, 1)):
            self.client.force_authenticate(usuario)
            resposta = self.client.get(url)
            self.assertEqual(resposta.status_code, status.HTTP_200_OK)
            self.assertEqual(resposta.data['count'], esperado, usuario.papel)

        self.client.force_authenticate(self.nutricionista)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_somente_diretor_e_tecnico_marcam_ciente(self):
        self.receber('100', 'Faltaram 400 kg.')
        pendencia = PendenciaFornecedor.objects.get()
        url = reverse('pendencia-fornecedor-ciente', args=[pendencia.id])

        self.client.force_authenticate(self.estoquista)
        self.assertEqual(self.client.post(url).status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.tecnico)
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data['status'], PendenciaFornecedor.Status.CIENTE)
        self.assertEqual(resposta.data['ciente_por'], self.tecnico.id)

        self.assertEqual(self.client.post(url).status_code, status.HTTP_400_BAD_REQUEST)

    def test_ordem_criada_pela_api_registra_o_solicitante(self):
        self.client.force_authenticate(self.tecnico)
        resposta = self.client.post(reverse('ordementrega-list'), {
            'empenho': self.empenho.id,
            'codigo': 'OE-NOVA',
            'data_entrega_prevista': '2026-02-01T00:00:00Z',
            'valor_total_executado': '0.00',
            'solicitante': self.diretor.id,
        }, format='json')

        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED, resposta.data)
        self.assertEqual(resposta.data['solicitante'], self.tecnico.id)


class EntregasProximasTests(EstoqueBaseMixin, APITestCase):
    """Consulta usada no aviso do Estoquista: ordens não concluídas com previsão até uma data."""

    def setUp(self):
        self.criar_cenario()
        self.parcial = OrdemEntrega.objects.create(
            empenho=self.empenho, codigo='OE-PARCIAL', status='par',
            data_entrega_prevista=datetime(2026, 1, 10, tzinfo=dt_timezone.utc),
            valor_total_executado=Decimal('0.00'),
        )
        OrdemEntrega.objects.create(
            empenho=self.empenho, codigo='OE-CONCLUIDA', status='con',
            data_entrega_prevista=datetime(2026, 1, 11, tzinfo=dt_timezone.utc),
            valor_total_executado=Decimal('0.00'),
        )
        OrdemEntrega.objects.create(
            empenho=self.empenho, codigo='OE-DISTANTE', status='esp',
            data_entrega_prevista=datetime(2026, 3, 1, tzinfo=dt_timezone.utc),
            valor_total_executado=Decimal('0.00'),
        )

    def test_estoquista_consulta_entregas_pendentes_ate_a_data(self):
        self.client.force_authenticate(self.estoquista)
        resposta = self.client.get(reverse('ordementrega-list'), {
            'status__in': 'esp,par',
            'data_entrega_prevista__lte': '2026-01-15T23:59:59Z',
            'ordering': 'data_entrega_prevista',
        })

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual([ordem['codigo'] for ordem in resposta.data['results']], ['OE-PARCIAL', 'OE-00030'])
