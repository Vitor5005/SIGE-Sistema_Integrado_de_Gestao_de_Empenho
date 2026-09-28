from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import DatabaseError, transaction
from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase

from cadastro.models import Endereco, Fornecedor, ItemGenerico
from empenho.models import Empenho, ItemEmpenho, OperacaoItem
from entrega.models import ItemOrdem, OrdemEntrega
from estoque.models import Estoque, MovimentacaoEstoque
from utils.estoque_services import (
    estornar_movimentacao,
    registrar_carga_inicial,
    registrar_recebimento,
    registrar_saida,
)
from licitacao.models import Ata, ItemAta, Licitacao
from usuario.models import Usuario
from utils.rbac import Acao, Papel, Recurso, tem_permissao


class EstoqueBaseMixin:
    def criar_cenario(self):
        self.diretor = Usuario.objects.create_user('diretor_est', password='senha', papel=Papel.DIRETOR)
        self.tecnico = Usuario.objects.create_user('tecnico_est', password='senha', papel=Papel.TECNICO_ADMINISTRATIVO)
        self.nutricionista = Usuario.objects.create_user('nutri_est', password='senha', papel=Papel.NUTRICIONISTA)
        self.estoquista = Usuario.objects.create_user('estoquista_est', password='senha', papel=Papel.ESTOQUISTA)
        endereco = Endereco.objects.create(
            lagradouro='Rua A', numero='1', bairro='Centro', cep='69900000',
            municipio='Rio Branco', estado='AC',
        )
        fornecedor = Fornecedor.objects.create(
            razao_social='T. LEITE SILVA', nome_fantasia='T. LEITE SILVA',
            cnpj='00.000.000/0001-00', endereco=endereco,
        )
        self.genero = ItemGenerico.objects.create(
            catmat='123456', descricao='Açúcar', unidade_medida='KG', categoria='SM',
        )
        licitacao = Licitacao.objects.create(
            numero_licitacao='109/2025', validade=12,
            data_abertura='2025-01-01', descricao='Teste de estoque',
        )
        ata = Ata.objects.create(
            numero_ata='109/2025', ata_saldo_total=Decimal('31200.00'),
            licitacao=licitacao, fornecedor=fornecedor,
        )
        item_ata = ItemAta.objects.create(
            ata=ata, item_generico=self.genero, marca='Marca',
            quantidade_licitada=Decimal('8000.00'), valor_unitario=Decimal('3.90'),
        )
        self.empenho = Empenho.objects.create(
            codigo='2025NE00030', ata=ata, valor_total=Decimal('9750.00'),
            saldo_utilizado=Decimal('0.00'),
        )
        self.item_empenho = ItemEmpenho.objects.create(
            empenho=self.empenho, item_ata=item_ata,
            quantidade_atual=Decimal('2000.00'), quantidade_entrege=Decimal('500.00'),
        )
        for tipo, valor in (('inc', '1000'), ('ref', '2000'), ('anl', '500')):
            OperacaoItem.objects.create(
                item_empenho=self.item_empenho, tipo=tipo, valor=Decimal(valor),
                data=datetime(2025, 1, 1, tzinfo=dt_timezone.utc),
            )
        self.ordem = OrdemEntrega.objects.create(
            empenho=self.empenho, codigo='OE-00030', status='esp',
            data_entrega_prevista=datetime(2026, 1, 12, tzinfo=dt_timezone.utc),
            valor_total_executado=Decimal('1950.00'),
        )
        self.item_ordem = ItemOrdem.objects.create(
            ordem_entrega=self.ordem, item_empenho=self.item_empenho,
            quantidade_solicitada=Decimal('500.00'), quantidade_entregue=Decimal('0.00'),
        )


class RegrasEstoqueTests(EstoqueBaseMixin, TestCase):
    def setUp(self):
        self.criar_cenario()

    def test_cenario_aceitacao_com_saldos_esperados(self):
        registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{'item_ordem_id': self.item_ordem.id, 'quantidade_recebida': '500'}],
            usuario=self.estoquista,
            data_entrada=datetime(2026, 1, 12, tzinfo=dt_timezone.utc),
        )
        registrar_saida(
            item_generico_id=self.genero.id, quantidade='50', tipo_saida='DOACAO',
            justificativa='Doação para o CAP', usuario=self.estoquista,
            data_hora=datetime(2026, 1, 13, tzinfo=dt_timezone.utc),
        )
        registrar_saida(
            item_generico_id=self.genero.id, quantidade='50', tipo_saida='PRODUCAO',
            justificativa='Produção de suco no almoço', usuario=self.estoquista,
            data_hora=datetime(2026, 1, 15, tzinfo=dt_timezone.utc),
        )

        self.item_empenho.refresh_from_db()
        self.empenho.refresh_from_db()
        self.ordem.refresh_from_db()
        self.assertEqual(self.item_empenho.quantidade_atual, Decimal('2000.00'))
        self.assertEqual(self.empenho.saldo_utilizado, Decimal('1950.00'))
        self.assertEqual(self.ordem.valor_total_executado, Decimal('1950.00'))
        self.assertEqual(Estoque.objects.get(item_generico=self.genero).saldo_atual, Decimal('400.000'))

        cliente = APIClient()
        cliente.force_authenticate(self.diretor)
        resposta = cliente.get(reverse('estoque-consolidado'))
        linha = resposta.data[0]
        self.assertEqual(Decimal(linha['saldo_ata']), Decimal('5500.00'))
        self.assertEqual(Decimal(linha['saldo_empenho']), Decimal('2000.00'))
        self.assertEqual(Decimal(linha['saldo_estoque']), Decimal('400.000'))

    def test_saida_maior_que_saldo_nao_grava(self):
        registrar_carga_inicial(
            item_generico_id=self.genero.id, quantidade='10', justificativa='Implantação',
            usuario=self.estoquista,
        )
        quantidade_antes = MovimentacaoEstoque.objects.count()
        with self.assertRaises(ValidationError):
            registrar_saida(
                item_generico_id=self.genero.id, quantidade='11', tipo_saida='PERDA',
                justificativa='Avaria', usuario=self.estoquista,
            )
        self.assertEqual(MovimentacaoEstoque.objects.count(), quantidade_antes)
        self.assertEqual(Estoque.objects.get(item_generico=self.genero).saldo_atual, Decimal('10.000'))

    def test_recebimento_maior_que_solicitado_e_rejeitado(self):
        with self.assertRaises(ValidationError):
            registrar_recebimento(
                ordem_id=self.ordem.id,
                itens_recebidos=[{'item_ordem_id': self.item_ordem.id, 'quantidade_recebida': '501'}],
                usuario=self.estoquista,
            )
        self.ordem.refresh_from_db()
        self.assertEqual(self.ordem.status, 'esp')
        self.assertFalse(MovimentacaoEstoque.objects.exists())

    def test_entrega_parcial_mantem_pendencia_e_segunda_entrega_conclui(self):
        registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'quantidade_recebida': '100',
                'observacao': 'Fornecedor entregara os 400 kg restantes depois.',
            }],
            usuario=self.estoquista,
        )
        self.ordem.refresh_from_db()
        self.item_ordem.refresh_from_db()
        self.assertEqual(self.ordem.status, 'par')
        self.assertEqual(self.item_ordem.quantidade_entregue, Decimal('100.00'))
        self.assertEqual(self.item_ordem.quantidade_pendente, Decimal('400.00'))
        self.assertEqual(Estoque.objects.get(item_generico=self.genero).saldo_atual, Decimal('100.000'))

        registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'quantidade_recebida': '400',
            }],
            usuario=self.estoquista,
        )
        self.ordem.refresh_from_db()
        self.item_ordem.refresh_from_db()
        self.assertEqual(self.ordem.status, 'con')
        self.assertEqual(self.item_ordem.quantidade_pendente, Decimal('0.00'))
        self.assertEqual(Estoque.objects.get(item_generico=self.genero).saldo_atual, Decimal('500.000'))
        self.assertEqual(
            MovimentacaoEstoque.objects.filter(item_ordem=self.item_ordem).count(), 2
        )

    def test_entrega_parcial_exige_motivo(self):
        with self.assertRaises(ValidationError):
            registrar_recebimento(
                ordem_id=self.ordem.id,
                itens_recebidos=[{
                    'item_ordem_id': self.item_ordem.id,
                    'quantidade_recebida': '100',
                }],
                usuario=self.estoquista,
            )
        self.item_ordem.refresh_from_db()
        self.assertEqual(self.item_ordem.quantidade_entregue, Decimal('0.00'))

    def test_falha_na_entrada_desfaz_conclusao_da_ordem(self):
        with patch('utils.estoque_services._registrar_movimentacao', side_effect=RuntimeError('falha simulada')):
            with self.assertRaises(RuntimeError):
                registrar_recebimento(
                    ordem_id=self.ordem.id,
                    itens_recebidos=[{'item_ordem_id': self.item_ordem.id, 'quantidade_recebida': '500'}],
                    usuario=self.estoquista,
                )
        self.ordem.refresh_from_db()
        self.item_ordem.refresh_from_db()
        self.assertEqual(self.ordem.status, 'esp')
        self.assertEqual(self.item_ordem.quantidade_entregue, Decimal('0.00'))

    def test_estorno_restaura_saldo_e_preserva_original(self):
        original = registrar_carga_inicial(
            item_generico_id=self.genero.id, quantidade='25', justificativa='Implantação',
            usuario=self.estoquista,
        )
        estorno = estornar_movimentacao(
            movimentacao_id=original.id, justificativa='Lançamento incorreto',
            usuario=self.estoquista,
        )
        self.assertTrue(MovimentacaoEstoque.objects.filter(pk=original.pk).exists())
        self.assertEqual(estorno.movimentacao_estornada, original)
        self.assertEqual(Estoque.objects.get(item_generico=self.genero).saldo_atual, Decimal('0.000'))

    def test_saldo_materializado_confere_com_livro_razao(self):
        registrar_carga_inicial(
            item_generico_id=self.genero.id, quantidade='100', justificativa='Implantação',
            usuario=self.estoquista,
        )
        registrar_saida(
            item_generico_id=self.genero.id, quantidade='35', tipo_saida='PRODUCAO',
            justificativa='Produção do almoço', usuario=self.estoquista,
        )
        saldo_razao = sum(
            movimento.quantidade if movimento.sentido == 'E' else -movimento.quantidade
            for movimento in MovimentacaoEstoque.objects.filter(estoque__item_generico=self.genero)
        )
        self.assertEqual(
            Estoque.objects.get(item_generico=self.genero).saldo_atual,
            saldo_razao,
        )

    def test_movimentacao_e_imutavel_na_aplicacao_e_no_banco(self):
        movimento = registrar_carga_inicial(
            item_generico_id=self.genero.id, quantidade='10', justificativa='Implantação',
            usuario=self.estoquista,
        )
        movimento.observacao = 'alterada'
        with self.assertRaises(DjangoValidationError):
            movimento.save()
        with self.assertRaises(DjangoValidationError):
            MovimentacaoEstoque.objects.filter(pk=movimento.pk).update(observacao='alterada')
        with self.assertRaises(DatabaseError), transaction.atomic():
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    'UPDATE estoque_movimentacaoestoque SET observacao=%s WHERE id=%s',
                    ['alterada', movimento.pk],
                )


class PermissoesEstoqueTests(EstoqueBaseMixin, APITestCase):
    def setUp(self):
        self.criar_cenario()

    def test_matriz_de_todos_os_endpoints_por_papel(self):
        papeis = (Papel.DIRETOR, Papel.TECNICO_ADMINISTRATIVO, Papel.NUTRICIONISTA, Papel.ESTOQUISTA)
        regras = (
            (Recurso.ESTOQUE, Acao.CONSULTAR, set(papeis)),
            (Recurso.ESTOQUE, Acao.CONSULTAR_CONSOLIDADO, {Papel.DIRETOR, Papel.TECNICO_ADMINISTRATIVO, Papel.ESTOQUISTA}),
            (Recurso.MOVIMENTACAO_ESTOQUE, Acao.CONSULTAR_EXTRATO, {Papel.DIRETOR, Papel.NUTRICIONISTA, Papel.ESTOQUISTA}),
            (Recurso.ESTOQUE, Acao.REGISTRAR_RECEBIMENTO, {Papel.ESTOQUISTA}),
            (Recurso.ESTOQUE, Acao.REGISTRAR_SAIDA, {Papel.ESTOQUISTA}),
            (Recurso.ESTOQUE, Acao.REGISTRAR_CARGA_INICIAL, {Papel.ESTOQUISTA}),
            (Recurso.ESTOQUE, Acao.REGISTRAR_AJUSTE, {Papel.ESTOQUISTA}),
            (Recurso.ESTOQUE, Acao.ESTORNAR, {Papel.ESTOQUISTA}),
        )
        for recurso, acao, permitidos in regras:
            for papel in papeis:
                with self.subTest(recurso=recurso, acao=acao, papel=papel):
                    self.assertEqual(tem_permissao(papel, recurso, acao), papel in permitidos)

    def test_consultas_respeitam_perfis(self):
        urls = (
            (reverse('estoque-list'), {Papel.DIRETOR, Papel.TECNICO_ADMINISTRATIVO, Papel.NUTRICIONISTA, Papel.ESTOQUISTA}),
            (reverse('estoque-consolidado'), {Papel.DIRETOR, Papel.TECNICO_ADMINISTRATIVO, Papel.ESTOQUISTA}),
            (reverse('movimentacao-estoque-list'), {Papel.DIRETOR, Papel.NUTRICIONISTA, Papel.ESTOQUISTA}),
        )
        usuarios = (self.diretor, self.tecnico, self.nutricionista, self.estoquista)
        for url, permitidos in urls:
            for usuario in usuarios:
                self.client.force_authenticate(usuario)
                resposta = self.client.get(url)
                esperado = 200 if usuario.papel in permitidos else 403
                self.assertEqual(resposta.status_code, esperado, (url, usuario.papel, resposta.data))

    def test_somente_estoquista_registra_saida(self):
        payload = {
            'item_generico_id': self.genero.id,
            'quantidade': '1',
            'tipo_saida': 'PERDA',
            'justificativa': 'Teste',
        }
        for usuario in (self.diretor, self.tecnico, self.nutricionista):
            self.client.force_authenticate(usuario)
            self.assertEqual(self.client.post(reverse('estoque-saidas'), payload, format='json').status_code, 403)



class InventarioTests(EstoqueBaseMixin, APITestCase):
    """Inventário recebe a quantidade contada; carga inicial só vale uma vez por gênero."""

    def setUp(self):
        self.criar_cenario()
        registrar_carga_inicial(
            item_generico_id=self.genero.id, quantidade='50', justificativa='Implantação',
            usuario=self.estoquista,
        )
        self.client.force_authenticate(self.estoquista)

    def inventariar(self, quantidade_contada):
        return self.client.post(reverse('estoque-ajustes'), {
            'item_generico_id': self.genero.id,
            'quantidade_contada': quantidade_contada,
            'justificativa': 'Contagem mensal',
        }, format='json')

    def test_contagem_menor_lanca_falta_pela_diferenca(self):
        resposta = self.inventariar('47')

        self.assertEqual(resposta.status_code, 201, resposta.data)
        self.assertEqual(resposta.data['tipo'], MovimentacaoEstoque.Tipo.AJUSTE_NEGATIVO)
        self.assertEqual(resposta.data['tipo_descricao'], 'Inventário (falta)')
        self.assertEqual(Decimal(resposta.data['quantidade']), Decimal('3'))
        self.assertEqual(Estoque.objects.get(item_generico=self.genero).saldo_atual, Decimal('47.000'))

    def test_contagem_maior_lanca_sobra(self):
        resposta = self.inventariar('52.5')

        self.assertEqual(resposta.status_code, 201, resposta.data)
        self.assertEqual(resposta.data['tipo'], MovimentacaoEstoque.Tipo.AJUSTE_POSITIVO)
        self.assertEqual(Estoque.objects.get(item_generico=self.genero).saldo_atual, Decimal('52.500'))

    def test_contagem_igual_ao_saldo_nao_gera_movimentacao(self):
        quantidade_antes = MovimentacaoEstoque.objects.count()
        resposta = self.inventariar('50')

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(MovimentacaoEstoque.objects.count(), quantidade_antes)

    def test_contagem_zero_zera_o_estoque_e_negativa_e_rejeitada(self):
        self.assertEqual(self.inventariar('-1').status_code, 400)
        self.assertEqual(self.inventariar('0').status_code, 201)
        self.assertEqual(Estoque.objects.get(item_generico=self.genero).saldo_atual, Decimal('0.000'))

    def test_listagem_indica_generos_que_ja_tem_carga_inicial(self):
        sem_carga = ItemGenerico.objects.create(
            catmat='654321', descricao='Feijão', unidade_medida='KG', categoria='NP',
        )
        dados = {
            item['item_generico_id']: item['possui_carga_inicial']
            for item in self.client.get(reverse('estoque-list'), {'page_size': 100}).data['results']
        }

        self.assertTrue(dados[self.genero.id])
        self.assertFalse(dados[sem_carga.id])


class PainelNutricionistaTests(EstoqueBaseMixin, APITestCase):
    """Home do Nutricionista: disponibilidade por gênero, movimentação semanal e saldos."""

    def setUp(self):
        self.criar_cenario()
        registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id, 'quantidade_recebida': '200',
                'observacao': 'Restante na próxima semana',
            }],
            usuario=self.estoquista,
        )
        registrar_saida(
            item_generico_id=self.genero.id, quantidade='50', tipo_saida='PRODUCAO',
            justificativa='Almoço', usuario=self.estoquista,
        )
        self.url = reverse('painel-nutricionista-list')

    def test_somente_nutricionista_acessa(self):
        for usuario in (self.diretor, self.tecnico, self.estoquista):
            self.client.force_authenticate(usuario)
            self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_disponibilidade_do_genero_do_estoque_ate_a_arp(self):
        self.client.force_authenticate(self.nutricionista)
        dados = self.client.get(self.url).data

        genero = next(g for g in dados['generos'] if g['item_generico_id'] == self.genero.id)
        self.assertEqual(genero['em_estoque'], Decimal('150.000'))
        self.assertEqual(genero['a_caminho'], Decimal('300.00'))
        self.assertEqual(genero['empenhado'], Decimal('2000.00'))
        self.assertEqual(genero['na_arp'], Decimal('5500.00'))

    def test_movimentacao_da_semana_atual_e_saldos_financeiros(self):
        self.client.force_authenticate(self.nutricionista)
        dados = self.client.get(self.url).data

        serie = dados['movimentacao']['por_genero'][self.genero.id]
        self.assertEqual(len(dados['movimentacao']['semanas']), 8)
        self.assertEqual(serie['entradas'][-1], Decimal('200.000'))
        self.assertEqual(serie['saidas'][-1], Decimal('50.000'))
        self.assertEqual(sum(serie['entradas'][:-1]), 0)

        empenho = dados['empenhos'][0]
        self.assertEqual(empenho['valor_utilizado'], Decimal('780.00'))
        self.assertEqual(empenho['saldo_disponivel'], Decimal('8970.00'))
        arp = dados['arps'][0]
        self.assertEqual(arp['valor_registrado'], Decimal('31200.00'))
        self.assertEqual(arp['saldo_disponivel'], Decimal('31200.00'))
