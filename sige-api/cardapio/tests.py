from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cadastro.models import ItemGenerico
from cardapio.models import Cardapio
from cardapio.serializers import hoje_no_ru
from estoque.models import Estoque, MovimentacaoEstoque
from usuario.models import Usuario
from utils.rbac import Papel


class CardapioFluxoTests(APITestCase):
    def setUp(self):
        self.nutricionista = Usuario.objects.create_user(
            username='nutri_cardapio', password='senha-segura', papel=Papel.NUTRICIONISTA,
        )
        self.estoquista = Usuario.objects.create_user(
            username='estoq_cardapio', password='senha-segura', papel=Papel.ESTOQUISTA,
        )
        self.arroz = ItemGenerico.objects.create(
            catmat='100001', descricao='Arroz', unidade_medida='KG', categoria='SM',
        )
        self.feijao = ItemGenerico.objects.create(
            catmat='100002', descricao='Feijão carioca', unidade_medida='KG', categoria='SM',
        )
        self._definir_saldo(self.arroz, '40')
        self._definir_saldo(self.feijao, '15')

    def _definir_saldo(self, genero, saldo):
        Estoque.objects.update_or_create(item_generico=genero, defaults={'saldo_atual': Decimal(saldo)})

    def _saldo(self, genero):
        return Estoque.objects.get(item_generico=genero).saldo_atual

    def _criar_cardapio(self, arroz='38', feijao='15'):
        resposta = self._post_cardapio(arroz, feijao)
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED, resposta.data)
        return resposta.data

    def _post_cardapio(self, arroz='38', feijao='15', data=None):
        self.client.force_authenticate(self.nutricionista)
        return self.client.post(reverse('cardapio-list'), {
            'refeicao': 'JANTAR',
            'data': (data or hoje_no_ru() + timedelta(days=1)).isoformat(),
            'estimativa_pessoas': 550,
            'preparacoes': 'ARROZ BRANCO\nFEIJÃO CARIOCA',
            'itens': [
                {'item_generico': self.arroz.id, 'quantidade_planejada': arroz, 'secao': ''},
                {'item_generico': self.feijao.id, 'quantidade_planejada': feijao, 'secao': '',
                 'observacao': '3 folhas de louro'},
            ],
        }, format='json')

    def _itens(self, cardapio):
        return {item['descricao']: item['id'] for item in cardapio['itens']}

    def test_fluxo_completo_acerta_o_estoque_pelo_consumo_real(self):
        cardapio = self._criar_cardapio()
        url = lambda nome: reverse(f'cardapio-{nome}', args=[cardapio['id']])
        itens = self._itens(cardapio)

        resposta = self.client.post(url('enviar'))
        self.assertEqual(resposta.data['status'], Cardapio.Status.ENVIADO)
        self.assertEqual(self._saldo(self.arroz), Decimal('40'))  # só reserva

        self.client.force_authenticate(self.estoquista)
        resposta = self.client.post(url('aprovar'), {'itens': [
            {'item': itens['Arroz'], 'quantidade': '25'},
            {'item': itens['Feijão carioca'], 'quantidade': '15'},
        ]}, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_200_OK, resposta.data)
        self.assertEqual(self._saldo(self.arroz), Decimal('15'))
        self.assertEqual(self._saldo(self.feijao), Decimal('0'))

        self.client.force_authenticate(self.nutricionista)
        resposta = self.client.post(url('informar-consumo'), {'itens': [
            {'item': itens['Arroz'], 'quantidade': '27'},  # usou 2 kg a mais
            {'item': itens['Feijão carioca'], 'quantidade': '12'},  # sobraram 3 kg
        ]}, format='json')
        self.assertEqual(resposta.data['status'], Cardapio.Status.CONSUMO_INFORMADO)
        self.assertEqual(self._saldo(self.arroz), Decimal('15'))  # nada muda antes da confirmação

        self.client.force_authenticate(self.estoquista)
        resposta = self.client.post(url('confirmar-consumo'))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK, resposta.data)
        self.assertEqual(resposta.data['status'], Cardapio.Status.FINALIZADO)
        self.assertEqual(self._saldo(self.arroz), Decimal('13'))
        self.assertEqual(self._saldo(self.feijao), Decimal('3'))
        self.assertTrue(MovimentacaoEstoque.objects.filter(
            tipo=MovimentacaoEstoque.Tipo.DEVOLUCAO_PREPARO, quantidade=Decimal('3'),
        ).exists())

    def test_nao_cria_cardapio_acima_do_saldo(self):
        resposta = self._post_cardapio(arroz='41')

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Arroz', str(resposta.data))
        self.assertFalse(Cardapio.objects.exists())

    def test_nao_cria_cardapio_com_genero_zerado(self):
        self._definir_saldo(self.feijao, '0')

        resposta = self._post_cardapio(feijao='1')

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Feijão carioca: sem saldo', str(resposta.data))

    def test_nao_cria_cardapio_com_data_no_passado(self):
        resposta = self._post_cardapio(data=hoje_no_ru() - timedelta(days=1))

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('data', resposta.data)
        self.assertFalse(Cardapio.objects.exists())

    def test_cria_cardapio_para_hoje(self):
        resposta = self._post_cardapio(data=hoje_no_ru())

        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED, resposta.data)

    def test_nao_cria_cardapio_sem_generos(self):
        self.client.force_authenticate(self.nutricionista)
        resposta = self.client.post(reverse('cardapio-list'), {
            'refeicao': 'JANTAR', 'data': hoje_no_ru().isoformat(), 'estimativa_pessoas': 550,
            'preparacoes': 'ARROZ BRANCO', 'itens': [],
        }, format='json')

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cardapio_enviado_reserva_o_saldo_para_os_demais(self):
        primeiro = self._criar_cardapio(arroz='30', feijao='1')
        self.client.post(reverse('cardapio-enviar', args=[primeiro['id']]))

        disponibilidade = self.client.get(reverse('cardapio-disponibilidade')).data
        arroz = next(item for item in disponibilidade if item['item_generico_id'] == self.arroz.id)
        self.assertEqual(Decimal(arroz['disponivel']), Decimal('10'))

        resposta = self._post_cardapio(arroz='20', feijao='1')
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_envio_recheca_o_saldo_de_cardapios_montados_ao_mesmo_tempo(self):
        primeiro = self._criar_cardapio(arroz='30', feijao='1')
        segundo = self._criar_cardapio(arroz='20', feijao='1')  # ainda não havia reserva

        self.client.post(reverse('cardapio-enviar', args=[primeiro['id']]))
        resposta = self.client.post(reverse('cardapio-enviar', args=[segundo['id']]))

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Cardapio.objects.get(pk=segundo['id']).status, Cardapio.Status.RASCUNHO)

    def test_recusa_devolve_para_edicao_e_libera_a_reserva(self):
        cardapio = self._criar_cardapio()
        self.client.post(reverse('cardapio-enviar', args=[cardapio['id']]))

        self.client.force_authenticate(self.estoquista)
        resposta = self.client.post(
            reverse('cardapio-recusar', args=[cardapio['id']]), {'motivo': 'Feijão reservado para o almoço.'},
        )
        self.assertEqual(resposta.data['status'], Cardapio.Status.RECUSADO)

        self.client.force_authenticate(self.nutricionista)
        resposta = self.client.patch(
            reverse('cardapio-detail', args=[cardapio['id']]), {'estimativa_pessoas': 500}, format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_estoquista_nao_libera_mais_que_o_planejado(self):
        cardapio = self._criar_cardapio(arroz='10')
        self.client.post(reverse('cardapio-enviar', args=[cardapio['id']]))
        itens = self._itens(cardapio)

        self.client.force_authenticate(self.estoquista)
        resposta = self.client.post(reverse('cardapio-aprovar', args=[cardapio['id']]), {'itens': [
            {'item': itens['Arroz'], 'quantidade': '12'},
        ]}, format='json')

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self._saldo(self.arroz), Decimal('40'))

    def test_cardapio_enviado_nao_pode_ser_editado(self):
        cardapio = self._criar_cardapio()
        self.client.post(reverse('cardapio-enviar', args=[cardapio['id']]))

        resposta = self.client.patch(
            reverse('cardapio-detail', args=[cardapio['id']]), {'estimativa_pessoas': 10}, format='json',
        )

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_papeis_respeitam_o_fluxo(self):
        cardapio = self._criar_cardapio()

        self.client.force_authenticate(self.estoquista)
        resposta = self.client.post(reverse('cardapio-list'), {}, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.nutricionista)
        self.client.post(reverse('cardapio-enviar', args=[cardapio['id']]))
        resposta = self.client.post(
            reverse('cardapio-aprovar', args=[cardapio['id']]), {'itens': [{'item': 1, 'quantidade': 1}]},
            format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_movimentacao_de_cardapio_nao_pode_ser_estornada_manualmente(self):
        cardapio = self._criar_cardapio()
        self.client.post(reverse('cardapio-enviar', args=[cardapio['id']]))
        self.client.force_authenticate(self.estoquista)
        itens = self._itens(cardapio)
        self.client.post(reverse('cardapio-aprovar', args=[cardapio['id']]), {'itens': [
            {'item': itens['Arroz'], 'quantidade': '38'},
        ]}, format='json')
        movimento = MovimentacaoEstoque.objects.filter(item_cardapio__isnull=False).first()

        resposta = self.client.post(reverse('estoque-estornos'), {
            'movimentacao_id': movimento.id, 'justificativa': 'Teste',
        }, format='json')

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    # ---- Alterações de última hora ----

    def _aprovar(self, cardapio, arroz='38', feijao='15'):
        self.client.force_authenticate(self.nutricionista)
        self.client.post(reverse('cardapio-enviar', args=[cardapio['id']]))
        itens = self._itens(cardapio)
        self.client.force_authenticate(self.estoquista)
        resposta = self.client.post(reverse('cardapio-aprovar', args=[cardapio['id']]), {'itens': [
            {'item': itens['Arroz'], 'quantidade': arroz},
            {'item': itens['Feijão carioca'], 'quantidade': feijao},
        ]}, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_200_OK, resposta.data)

    def test_cancelar_envio_volta_a_rascunho_e_libera_a_reserva(self):
        cardapio = self._criar_cardapio(arroz='30', feijao='1')
        self.client.post(reverse('cardapio-enviar', args=[cardapio['id']]))

        resposta = self.client.post(reverse('cardapio-cancelar-envio', args=[cardapio['id']]))

        self.assertEqual(resposta.status_code, status.HTTP_200_OK, resposta.data)
        self.assertEqual(resposta.data['status'], Cardapio.Status.RASCUNHO)
        self.assertIsNone(resposta.data['enviado_em'])
        self.assertEqual(self._post_cardapio(arroz='20', feijao='1').status_code, status.HTTP_201_CREATED)
        resposta = self.client.patch(
            reverse('cardapio-detail', args=[cardapio['id']]), {'estimativa_pessoas': 500}, format='json',
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_estoquista_nao_cancela_envio_e_aprovado_nao_pode_ser_cancelado(self):
        cardapio = self._criar_cardapio()
        self.client.post(reverse('cardapio-enviar', args=[cardapio['id']]))
        self.client.force_authenticate(self.estoquista)
        resposta = self.client.post(reverse('cardapio-cancelar-envio', args=[cardapio['id']]))
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

        self._aprovar(cardapio)
        self.client.force_authenticate(self.nutricionista)
        resposta = self.client.post(reverse('cardapio-cancelar-envio', args=[cardapio['id']]))
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_alteracao_aceita_devolve_o_liberado_e_cria_rascunho_igual(self):
        cardapio = self._criar_cardapio()
        self._aprovar(cardapio, arroz='30', feijao='15')
        self.assertEqual(self._saldo(self.arroz), Decimal('10'))

        self.client.force_authenticate(self.nutricionista)
        resposta = self.client.post(
            reverse('cardapio-solicitar-alteracao', args=[cardapio['id']]), {'motivo': 'Trocar o feijão.'},
        )
        self.assertEqual(resposta.data['status'], Cardapio.Status.ALTERACAO_SOLICITADA)
        self.assertEqual(resposta.data['motivo_alteracao'], 'Trocar o feijão.')
        self.assertEqual(self._saldo(self.arroz), Decimal('10'))  # nada volta antes do aceite

        self.client.force_authenticate(self.estoquista)
        resposta = self.client.post(reverse('cardapio-aceitar-alteracao', args=[cardapio['id']]))

        self.assertEqual(resposta.status_code, status.HTTP_200_OK, resposta.data)
        novo = resposta.data
        self.assertEqual(novo['status'], Cardapio.Status.RASCUNHO)
        self.assertEqual(novo['substitui'], cardapio['id'])
        self.assertEqual(
            {item['descricao']: Decimal(item['quantidade_planejada']) for item in novo['itens']},
            {'Arroz': Decimal('38'), 'Feijão carioca': Decimal('15')},
        )
        self.assertEqual(self._saldo(self.arroz), Decimal('40'))
        self.assertEqual(self._saldo(self.feijao), Decimal('15'))
        original = Cardapio.objects.get(pk=cardapio['id'])
        self.assertEqual(original.status, Cardapio.Status.SUBSTITUIDO)
        self.assertEqual(original.substituido_por_id, novo['id'])
        self.assertEqual(MovimentacaoEstoque.objects.filter(
            tipo=MovimentacaoEstoque.Tipo.DEVOLUCAO_PREPARO, item_cardapio__cardapio=original,
        ).count(), 2)

        # O rascunho segue o fluxo normal: é editado e reenviado.
        self.client.force_authenticate(self.nutricionista)
        resposta = self.client.patch(reverse('cardapio-detail', args=[novo['id']]), {
            'itens': [{'item_generico': self.arroz.id, 'quantidade_planejada': '40', 'secao': ''}],
        }, format='json')
        self.assertEqual(resposta.status_code, status.HTTP_200_OK, resposta.data)
        resposta = self.client.post(reverse('cardapio-enviar', args=[novo['id']]))
        self.assertEqual(resposta.data['status'], Cardapio.Status.ENVIADO)

    def test_alteracao_recusada_volta_a_aprovado_sem_mexer_no_estoque(self):
        cardapio = self._criar_cardapio()
        self._aprovar(cardapio)
        self.client.force_authenticate(self.nutricionista)
        self.client.post(reverse('cardapio-solicitar-alteracao', args=[cardapio['id']]), {'motivo': 'Trocar.'})

        self.client.force_authenticate(self.estoquista)
        resposta = self.client.post(
            reverse('cardapio-recusar-alteracao', args=[cardapio['id']]), {'motivo': 'Já está na panela.'},
        )

        self.assertEqual(resposta.data['status'], Cardapio.Status.APROVADO)
        self.assertEqual(resposta.data['motivo_recusa'], 'Já está na panela.')
        self.assertEqual(self._saldo(self.arroz), Decimal('2'))
        self.assertFalse(Cardapio.objects.filter(status=Cardapio.Status.RASCUNHO).exists())

    def test_nao_solicita_alteracao_de_cardapio_de_dia_passado(self):
        cardapio = self._criar_cardapio()
        self._aprovar(cardapio)
        Cardapio.objects.filter(pk=cardapio['id']).update(data=hoje_no_ru() - timedelta(days=1))

        self.client.force_authenticate(self.nutricionista)
        resposta = self.client.post(
            reverse('cardapio-solicitar-alteracao', args=[cardapio['id']]), {'motivo': 'Trocar.'},
        )

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_papeis_no_pedido_de_alteracao(self):
        cardapio = self._criar_cardapio()
        self._aprovar(cardapio)
        resposta = self.client.post(
            reverse('cardapio-solicitar-alteracao', args=[cardapio['id']]), {'motivo': 'Trocar.'},
        )
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.nutricionista)
        self.client.post(reverse('cardapio-solicitar-alteracao', args=[cardapio['id']]), {'motivo': 'Trocar.'})
        resposta = self.client.post(reverse('cardapio-aceitar-alteracao', args=[cardapio['id']]))
        self.assertEqual(resposta.status_code, status.HTTP_403_FORBIDDEN)

    def test_pendentes_mostram_o_que_aguarda_cada_papel(self):
        self._criar_cardapio(arroz='1', feijao='1')  # rascunho comum não é pendência
        cardapio = self._criar_cardapio(arroz='38', feijao='14')
        self._aprovar(cardapio, feijao='14')
        self.client.force_authenticate(self.nutricionista)
        self.client.post(reverse('cardapio-solicitar-alteracao', args=[cardapio['id']]), {'motivo': 'Trocar.'})

        self.client.force_authenticate(self.estoquista)
        pendentes = self.client.get(reverse('cardapio-list'), {'pendentes': 1}).data['results']
        self.assertEqual([item['id'] for item in pendentes], [cardapio['id']])

        novo = self.client.post(reverse('cardapio-aceitar-alteracao', args=[cardapio['id']])).data
        self.assertEqual(self.client.get(reverse('cardapio-list'), {'pendentes': 1}).data['count'], 0)

        self.client.force_authenticate(self.nutricionista)
        pendentes = self.client.get(reverse('cardapio-list'), {'pendentes': 1}).data['results']
        self.assertEqual([item['id'] for item in pendentes], [novo['id']])
