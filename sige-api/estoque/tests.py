from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
import threading
from unittest import skipUnless
from unittest.mock import patch

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import DatabaseError, close_old_connections, connection, transaction
from django.db.models import Sum
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase

from cadastro.models import Endereco, Fornecedor, ItemGenerico
from empenho.models import Empenho, ItemEmpenho, OperacaoItem
from entrega.models import ItemOrdem, OrdemEntrega
from estoque.models import (
    ContagemLoteInventario,
    Estoque,
    Inventario,
    LoteEstoque,
    MovimentacaoEstoque,
    MovimentacaoLote,
)
from estoque.serializers import LoteValidadeSerializer
from utils.estoque_services import (
    STATUS_VALIDADE_DESCRICOES,
    dias_para_data_validade,
    dias_para_validade,
    estornar_movimentacao,
    registrar_ajuste,
    registrar_carga_inicial,
    registrar_recebimento,
    registrar_saida,
    FUSO_ESTOQUE,
    data_atual_estoque,
    saldo_utilizavel_estoque,
    saldos_utilizaveis_por_estoque,
    status_data_validade,
    status_lote_validade,
)
from licitacao.models import Ata, ItemAta, Licitacao
from usuario.models import Usuario
from utils.painel_nutricionista import montar_painel
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

    def lote_recebimento(
        self,
        quantidade,
        numero='LOTE-TESTE-001',
        validade='2099-12-31',
    ):
        return {
            'numero_lote': numero,
            'data_validade': validade,
            'quantidade': quantidade,
        }

    def registrar_carga_teste(
        self,
        quantidade,
        numero='INICIAL-TESTE-001',
        validade='2099-12-31',
        item_generico_id=None,
        **kwargs,
    ):
        return registrar_carga_inicial(
            item_generico_id=item_generico_id or self.genero.id,
            lotes=[self.lote_recebimento(quantidade, numero=numero, validade=validade)],
            justificativa=kwargs.pop('justificativa', 'Implantação'),
            usuario=kwargs.pop('usuario', self.estoquista),
            **kwargs,
        )

    def lote_estoque(self, numero, saldo, validade=None, legado=False):
        estoque = Estoque.objects.get(item_generico=self.genero)
        saldo = Decimal(str(saldo)).quantize(Decimal('0.001'))
        if legado:
            lote, _ = LoteEstoque.objects.get_or_create(
                estoque=estoque,
                numero_lote=LoteEstoque.NUMERO_LOTE_LEGADO,
                defaults={
                    'data_validade': None,
                    'saldo_atual': Decimal('0.000'),
                    'legado': True,
                },
            )
            lote.saldo_atual = saldo
            lote.save(update_fields=['saldo_atual', 'data_atualizacao'])
        else:
            lote = LoteEstoque.objects.create(
                estoque=estoque,
                numero_lote=numero,
                data_validade=validade,
                saldo_atual=saldo,
                legado=False,
            )
        total = LoteEstoque.objects.filter(estoque=estoque).aggregate(total=Sum('saldo_atual'))['total']
        Estoque.objects.filter(pk=estoque.pk).update(saldo_atual=total or Decimal('0.000'))
        return lote

    def assert_integridade_estoque(self, estoque):
        precisao = Decimal('0.001')
        estoque.refresh_from_db()
        lotes = list(LoteEstoque.objects.filter(estoque=estoque))
        saldo_lotes = sum((lote.saldo_atual for lote in lotes), Decimal('0.000')).quantize(precisao)
        self.assertEqual(saldo_lotes, estoque.saldo_atual.quantize(precisao))

        movimentos = list(
            MovimentacaoEstoque.objects.filter(estoque=estoque)
            .prefetch_related('alocacoes_lote__lote')
        )
        saldo_razao_estoque = Decimal('0.000')
        saldo_razao_lotes = {lote.id: Decimal('0.000') for lote in lotes}
        for movimento in movimentos:
            alocacoes = list(movimento.alocacoes_lote.all())
            self.assertTrue(alocacoes)
            quantidade_alocada = sum(
                (alocacao.quantidade for alocacao in alocacoes),
                Decimal('0.000'),
            ).quantize(precisao)
            self.assertEqual(quantidade_alocada, movimento.quantidade.quantize(precisao))

            sinal = Decimal('1') if movimento.sentido == MovimentacaoEstoque.Sentido.ENTRADA else Decimal('-1')
            saldo_razao_estoque += sinal * movimento.quantidade
            for alocacao in alocacoes:
                self.assertEqual(alocacao.lote.estoque_id, estoque.id)
                saldo_razao_lotes[alocacao.lote_id] = (
                    saldo_razao_lotes.get(alocacao.lote_id, Decimal('0.000'))
                    + sinal * alocacao.quantidade
                )

        self.assertEqual(
            saldo_razao_estoque.quantize(precisao),
            estoque.saldo_atual.quantize(precisao),
        )
        for lote in lotes:
            self.assertEqual(
                saldo_razao_lotes.get(lote.id, Decimal('0.000')).quantize(precisao),
                lote.saldo_atual.quantize(precisao),
            )


class RegrasEstoqueTests(EstoqueBaseMixin, TestCase):
    def setUp(self):
        self.criar_cenario()

    def test_cenario_aceitacao_com_saldos_esperados(self):
        registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'lotes': [self.lote_recebimento('500')],
            }],
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
        self.registrar_carga_teste(
            item_generico_id=self.genero.id, quantidade='10', justificativa='Implantação',
            usuario=self.estoquista,
        )
        lote = LoteEstoque.objects.get(
            estoque__item_generico=self.genero,
            legado=False,
        )
        quantidade_antes = MovimentacaoEstoque.objects.count()
        with self.assertRaises(ValidationError):
            registrar_saida(
                item_generico_id=self.genero.id, quantidade='11', tipo_saida='PERDA',
                justificativa='Avaria', usuario=self.estoquista, lote_id=lote.id,
            )
        self.assertEqual(MovimentacaoEstoque.objects.count(), quantidade_antes)
        self.assertEqual(Estoque.objects.get(item_generico=self.genero).saldo_atual, Decimal('10.000'))

    def test_recebimento_maior_que_solicitado_e_rejeitado(self):
        with self.assertRaises(ValidationError):
            registrar_recebimento(
                ordem_id=self.ordem.id,
                itens_recebidos=[{
                    'item_ordem_id': self.item_ordem.id,
                    'lotes': [
                        self.lote_recebimento('300', numero='LOTE-A'),
                        self.lote_recebimento('201', numero='LOTE-B'),
                    ],
                }],
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
                'lotes': [self.lote_recebimento('100')],
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
                'lotes': [self.lote_recebimento('400')],
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
                    'lotes': [self.lote_recebimento('100')],
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
                    itens_recebidos=[{
                        'item_ordem_id': self.item_ordem.id,
                        'lotes': [self.lote_recebimento('500')],
                    }],
                    usuario=self.estoquista,
                )
        self.ordem.refresh_from_db()
        self.item_ordem.refresh_from_db()
        self.assertEqual(self.ordem.status, 'esp')
        self.assertEqual(self.item_ordem.quantidade_entregue, Decimal('0.00'))

    def test_estorno_restaura_saldo_e_preserva_original(self):
        original = self.registrar_carga_teste(
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
        self.registrar_carga_teste(
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
        movimento = self.registrar_carga_teste(
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

    def test_recebimento_pode_distribuir_item_em_multiplos_lotes(self):
        _, movimentos = registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'lotes': [
                    self.lote_recebimento('200', numero='LOTE-A'),
                    self.lote_recebimento('300', numero='LOTE-B'),
                ],
            }],
            usuario=self.estoquista,
        )

        estoque = Estoque.objects.get(item_generico=self.genero)
        lote_a = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-A')
        lote_b = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-B')
        movimento = movimentos[0]

        self.assertEqual(estoque.saldo_atual, Decimal('500.000'))
        self.assertEqual(lote_a.saldo_atual, Decimal('200.000'))
        self.assertEqual(lote_b.saldo_atual, Decimal('300.000'))
        self.assertEqual(MovimentacaoEstoque.objects.count(), 1)
        self.assertEqual(movimento.quantidade, Decimal('500.000'))
        self.assertEqual(movimento.alocacoes_lote.count(), 2)
        self.assertEqual(
            sum(
                movimento.alocacoes_lote.values_list('quantidade', flat=True),
                Decimal('0.000'),
            ),
            Decimal('500.000'),
        )

    def test_novo_recebimento_do_mesmo_lote_acumula_saldo(self):
        registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'lotes': [self.lote_recebimento('100', numero='ABC')],
                'observacao': 'Complemento pendente.',
            }],
            usuario=self.estoquista,
        )
        registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'lotes': [self.lote_recebimento('400', numero='ABC')],
            }],
            usuario=self.estoquista,
        )

        estoque = Estoque.objects.get(item_generico=self.genero)
        lote = LoteEstoque.objects.get(estoque=estoque, numero_lote='ABC')
        self.ordem.refresh_from_db()

        self.assertEqual(LoteEstoque.objects.filter(estoque=estoque, numero_lote__iexact='ABC').count(), 1)
        self.assertEqual(lote.saldo_atual, Decimal('500.000'))
        self.assertEqual(self.ordem.status, 'con')

    def test_mesmo_numero_de_lote_com_validade_diferente_e_rejeitado(self):
        registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'lotes': [self.lote_recebimento('100', numero='ABC', validade='2099-12-31')],
                'observacao': 'Complemento pendente.',
            }],
            usuario=self.estoquista,
        )
        movimentos_antes = MovimentacaoEstoque.objects.count()

        with self.assertRaises(ValidationError):
            registrar_recebimento(
                ordem_id=self.ordem.id,
                itens_recebidos=[{
                    'item_ordem_id': self.item_ordem.id,
                    'lotes': [self.lote_recebimento('400', numero='ABC', validade='2099-11-30')],
                }],
                usuario=self.estoquista,
            )

        self.item_ordem.refresh_from_db()
        estoque = Estoque.objects.get(item_generico=self.genero)
        lote = LoteEstoque.objects.get(estoque=estoque, numero_lote='ABC')
        self.assertEqual(self.item_ordem.quantidade_entregue, Decimal('100.00'))
        self.assertEqual(estoque.saldo_atual, Decimal('100.000'))
        self.assertEqual(lote.saldo_atual, Decimal('100.000'))
        self.assertEqual(MovimentacaoEstoque.objects.count(), movimentos_antes)

    def test_recebimento_rejeita_lote_duplicado_no_mesmo_item(self):
        with self.assertRaises(ValidationError):
            registrar_recebimento(
                ordem_id=self.ordem.id,
                itens_recebidos=[{
                    'item_ordem_id': self.item_ordem.id,
                    'lotes': [
                        self.lote_recebimento('200', numero='ABC'),
                        self.lote_recebimento('300', numero='abc'),
                    ],
                }],
                usuario=self.estoquista,
            )

        self.assertFalse(MovimentacaoEstoque.objects.exists())

    def test_recebimento_rejeita_numero_lote_legado(self):
        for numero_lote in ('LEGADO', 'legado'):
            with self.subTest(numero_lote=numero_lote):
                with self.assertRaises(ValidationError):
                    registrar_recebimento(
                        ordem_id=self.ordem.id,
                        itens_recebidos=[{
                            'item_ordem_id': self.item_ordem.id,
                            'lotes': [self.lote_recebimento('500', numero=numero_lote)],
                        }],
                        usuario=self.estoquista,
                    )
        self.assertFalse(MovimentacaoEstoque.objects.exists())

    def test_recebimento_rejeita_lote_vencido_antes_da_entrada(self):
        data_entrada = datetime(2026, 10, 30, 12, tzinfo=dt_timezone.utc)
        with self.assertRaises(ValidationError):
            registrar_recebimento(
                ordem_id=self.ordem.id,
                itens_recebidos=[{
                    'item_ordem_id': self.item_ordem.id,
                    'lotes': [self.lote_recebimento('500', validade='2026-10-29')],
                }],
                usuario=self.estoquista,
                data_entrada=data_entrada,
            )

        self.assertFalse(MovimentacaoEstoque.objects.exists())
        registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'lotes': [self.lote_recebimento('500', validade='2026-10-30')],
            }],
            usuario=self.estoquista,
            data_entrada=data_entrada,
        )
        self.assertEqual(Estoque.objects.get(item_generico=self.genero).saldo_atual, Decimal('500.000'))

    def test_validade_do_lote_considera_data_local_de_rio_branco(self):
        data_entrada = datetime(2026, 10, 31, 2, tzinfo=dt_timezone.utc)
        _, movimentos = registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'lotes': [self.lote_recebimento(
                    '100',
                    numero='LOTE-RIO-BRANCO-001',
                    validade='2026-10-30',
                )],
                'observacao': 'Entrega parcial para validar a data operacional.',
            }],
            usuario=self.estoquista,
            data_entrada=data_entrada,
        )

        estoque = Estoque.objects.get(item_generico=self.genero)
        lote = LoteEstoque.objects.get(
            estoque=estoque,
            numero_lote='LOTE-RIO-BRANCO-001',
        )
        self.assertEqual(movimentos[0].quantidade, Decimal('100.000'))
        self.assertEqual(estoque.saldo_atual, Decimal('100.000'))
        self.assertEqual(lote.saldo_atual, Decimal('100.000'))

        with self.assertRaises(ValidationError):
            registrar_recebimento(
                ordem_id=self.ordem.id,
                itens_recebidos=[{
                    'item_ordem_id': self.item_ordem.id,
                    'lotes': [self.lote_recebimento(
                        '400',
                        numero='LOTE-RIO-BRANCO-002',
                        validade='2026-10-29',
                    )],
                }],
                usuario=self.estoquista,
                data_entrada=data_entrada,
            )

        self.assertEqual(Estoque.objects.get(item_generico=self.genero).saldo_atual, Decimal('100.000'))

    def test_estorno_de_recebimento_reverte_os_mesmos_lotes(self):
        _, movimentos = registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'lotes': [
                    self.lote_recebimento('200', numero='LOTE-A'),
                    self.lote_recebimento('300', numero='LOTE-B'),
                ],
            }],
            usuario=self.estoquista,
        )
        original = movimentos[0]
        estorno = estornar_movimentacao(
            movimentacao_id=original.id,
            justificativa='Recebimento informado incorretamente.',
            usuario=self.estoquista,
        )

        estoque = Estoque.objects.get(item_generico=self.genero)
        lote_a = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-A')
        lote_b = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-B')
        self.assertEqual(estoque.saldo_atual, Decimal('0.000'))
        self.assertEqual(lote_a.saldo_atual, Decimal('0.000'))
        self.assertEqual(lote_b.saldo_atual, Decimal('0.000'))
        self.assertEqual(
            set(estorno.alocacoes_lote.values_list('lote__numero_lote', 'quantidade')),
            {('LOTE-A', Decimal('200.000')), ('LOTE-B', Decimal('300.000'))},
        )
        self.assertFalse(
            estorno.alocacoes_lote.filter(lote__numero_lote=LoteEstoque.NUMERO_LOTE_LEGADO).exists()
        )

    def test_estorno_de_entrada_rejeitado_se_lote_ja_foi_consumido(self):
        _, movimentos = registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'lotes': [self.lote_recebimento('100', numero='LOTE-A')],
                'observacao': 'Complemento pendente.',
            }],
            usuario=self.estoquista,
        )
        original = movimentos[0]
        registrar_saida(
            item_generico_id=self.genero.id,
            quantidade='20',
            tipo_saida='PRODUCAO',
            justificativa='Consumo de teste.',
            usuario=self.estoquista,
        )

        with self.assertRaises(ValidationError):
            estornar_movimentacao(
                movimentacao_id=original.id,
                justificativa='Tentativa de estorno.',
                usuario=self.estoquista,
            )

        estoque = Estoque.objects.get(item_generico=self.genero)
        lote = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-A')
        self.assertEqual(estoque.saldo_atual, Decimal('80.000'))
        self.assertEqual(lote.saldo_atual, Decimal('80.000'))
        self.assertFalse(MovimentacaoEstoque.objects.filter(movimentacao_estornada=original).exists())

    def test_movimentacao_lote_e_imutavel(self):
        movimento = self.registrar_carga_teste(
            item_generico_id=self.genero.id,
            quantidade='10',
            justificativa='Implantação',
            usuario=self.estoquista,
        )
        alocacao = movimento.alocacoes_lote.get()

        alocacao.quantidade = Decimal('1')
        with self.assertRaises(DjangoValidationError):
            alocacao.save()
        with self.assertRaises(DjangoValidationError):
            MovimentacaoLote.objects.filter(pk=alocacao.pk).update(quantidade=Decimal('1'))
        with self.assertRaises(DatabaseError), transaction.atomic():
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    'UPDATE estoque_movimentacaolote SET quantidade=%s WHERE id=%s',
                    [Decimal('1'), alocacao.pk],
                )

    def test_saida_producao_utiliza_fefo(self):
        lote_a = self.lote_estoque('LOTE-A', '20', date(2099, 1, 1))
        lote_b = self.lote_estoque('LOTE-B', '50', date(2099, 2, 1))
        lote_c = self.lote_estoque('LOTE-C', '100', date(2099, 3, 1))

        movimento = registrar_saida(
            item_generico_id=self.genero.id,
            quantidade='60',
            tipo_saida='PRODUCAO',
            justificativa='Uso em producao.',
            usuario=self.estoquista,
            data_hora=datetime(2098, 1, 1, 12, tzinfo=dt_timezone.utc),
        )

        lote_a.refresh_from_db()
        lote_b.refresh_from_db()
        lote_c.refresh_from_db()
        self.assertEqual(lote_a.saldo_atual, Decimal('0.000'))
        self.assertEqual(lote_b.saldo_atual, Decimal('10.000'))
        self.assertEqual(lote_c.saldo_atual, Decimal('100.000'))
        self.assertEqual(movimento.quantidade, Decimal('60.000'))
        self.assertEqual(
            set(movimento.alocacoes_lote.values_list('lote_id', 'quantidade')),
            {(lote_a.id, Decimal('20.000')), (lote_b.id, Decimal('40.000'))},
        )

    def test_fefo_utiliza_legado_somente_depois_dos_lotes_reais_validos(self):
        lote_legado = self.lote_estoque('LEGADO', '50', legado=True)
        lote_a = self.lote_estoque('LOTE-A', '40', date(2099, 1, 1))
        lote_b = self.lote_estoque('LOTE-B', '30', date(2099, 2, 1))

        registrar_saida(
            item_generico_id=self.genero.id,
            quantidade='60',
            tipo_saida='PRODUCAO',
            justificativa='Uso em producao.',
            usuario=self.estoquista,
            data_hora=datetime(2098, 1, 1, 12, tzinfo=dt_timezone.utc),
        )

        lote_legado.refresh_from_db()
        lote_a.refresh_from_db()
        lote_b.refresh_from_db()
        self.assertEqual(lote_a.saldo_atual, Decimal('0.000'))
        self.assertEqual(lote_b.saldo_atual, Decimal('10.000'))
        self.assertEqual(lote_legado.saldo_atual, Decimal('50.000'))

    def test_saida_producao_nao_utiliza_lote_vencido(self):
        vencido = self.lote_estoque('LOTE-VENCIDO', '100', date(2026, 10, 29))
        valido = self.lote_estoque('LOTE-VALIDO', '20', date(2026, 10, 31))
        movimentos_antes = MovimentacaoEstoque.objects.count()

        with self.assertRaises(ValidationError):
            registrar_saida(
                item_generico_id=self.genero.id,
                quantidade='30',
                tipo_saida='PRODUCAO',
                justificativa='Uso em producao.',
                usuario=self.estoquista,
                data_hora=datetime(2026, 10, 30, 12, tzinfo=dt_timezone.utc),
            )

        vencido.refresh_from_db()
        valido.refresh_from_db()
        self.assertEqual(vencido.saldo_atual, Decimal('100.000'))
        self.assertEqual(valido.saldo_atual, Decimal('20.000'))
        self.assertEqual(MovimentacaoEstoque.objects.count(), movimentos_antes)

    def test_saida_doacao_utiliza_fefo_e_ignora_vencidos(self):
        vencido = self.lote_estoque('LOTE-VENCIDO', '100', date(2026, 10, 29))
        lote_a = self.lote_estoque('LOTE-A', '10', date(2026, 10, 30))
        lote_b = self.lote_estoque('LOTE-B', '50', date(2026, 11, 1))

        registrar_saida(
            item_generico_id=self.genero.id,
            quantidade='15',
            tipo_saida='DOACAO',
            justificativa='Doacao autorizada.',
            usuario=self.estoquista,
            data_hora=datetime(2026, 10, 30, 12, tzinfo=dt_timezone.utc),
        )

        vencido.refresh_from_db()
        lote_a.refresh_from_db()
        lote_b.refresh_from_db()
        self.assertEqual(vencido.saldo_atual, Decimal('100.000'))
        self.assertEqual(lote_a.saldo_atual, Decimal('0.000'))
        self.assertEqual(lote_b.saldo_atual, Decimal('45.000'))

    def test_perda_requer_e_movimenta_apenas_lote_informado(self):
        lote_a = self.lote_estoque('LOTE-VENCIDO', '30', date(2026, 10, 29))
        lote_b = self.lote_estoque('LOTE-VALIDO', '100', date(2026, 12, 1))

        movimento = registrar_saida(
            item_generico_id=self.genero.id,
            quantidade='20',
            tipo_saida='PERDA',
            lote_id=lote_a.id,
            justificativa='Avaria no lote.',
            usuario=self.estoquista,
            data_hora=datetime(2026, 10, 30, 12, tzinfo=dt_timezone.utc),
        )

        estoque = Estoque.objects.get(item_generico=self.genero)
        lote_a.refresh_from_db()
        lote_b.refresh_from_db()
        self.assertEqual(lote_a.saldo_atual, Decimal('10.000'))
        self.assertEqual(lote_b.saldo_atual, Decimal('100.000'))
        self.assertEqual(estoque.saldo_atual, Decimal('110.000'))
        self.assertEqual(movimento.alocacoes_lote.count(), 1)
        self.assertEqual(movimento.alocacoes_lote.get().lote_id, lote_a.id)

    def test_perda_sem_lote_e_rejeitada(self):
        self.lote_estoque('LOTE-A', '30', date(2026, 12, 1))
        movimentos_antes = MovimentacaoEstoque.objects.count()

        with self.assertRaises(ValidationError):
            registrar_saida(
                item_generico_id=self.genero.id,
                quantidade='20',
                tipo_saida='PERDA',
                justificativa='Avaria no lote.',
                usuario=self.estoquista,
            )

        self.assertEqual(MovimentacaoEstoque.objects.count(), movimentos_antes)

    def test_perda_maior_que_saldo_do_lote_e_rejeitada(self):
        lote_a = self.lote_estoque('LOTE-A', '10', date(2026, 12, 1))
        lote_b = self.lote_estoque('LOTE-B', '100', date(2026, 12, 2))
        movimentos_antes = MovimentacaoEstoque.objects.count()

        with self.assertRaises(ValidationError):
            registrar_saida(
                item_generico_id=self.genero.id,
                quantidade='20',
                tipo_saida='PERDA',
                lote_id=lote_a.id,
                justificativa='Avaria no lote.',
                usuario=self.estoquista,
            )

        lote_a.refresh_from_db()
        lote_b.refresh_from_db()
        self.assertEqual(lote_a.saldo_atual, Decimal('10.000'))
        self.assertEqual(lote_b.saldo_atual, Decimal('100.000'))
        self.assertEqual(MovimentacaoEstoque.objects.count(), movimentos_antes)

    def test_saldo_utilizavel_exclui_lotes_vencidos_e_aparece_na_listagem(self):
        hoje = timezone.localtime(timezone.now(), FUSO_ESTOQUE).date()
        self.lote_estoque('LOTE-VENCIDO', '30', hoje - timedelta(days=1))
        self.lote_estoque('LOTE-VALIDO', '50', hoje)
        self.lote_estoque('LEGADO', '20', legado=True)
        estoque = Estoque.objects.get(item_generico=self.genero)

        self.assertEqual(estoque.saldo_atual, Decimal('100.000'))
        self.assertEqual(saldo_utilizavel_estoque(estoque, hoje), Decimal('70.000'))

        cliente = APIClient()
        cliente.force_authenticate(self.diretor)
        resposta = cliente.get(reverse('estoque-list'), {'page_size': 100})
        linha = next(
            item for item in resposta.data['results']
            if item['item_generico_id'] == self.genero.id
        )
        self.assertEqual(Decimal(linha['saldo_atual']), Decimal('100.000'))
        self.assertEqual(Decimal(linha['saldo_utilizavel']), Decimal('70.000'))


    def test_novo_genero_cria_estoque_sem_lote_legado(self):
        genero = ItemGenerico.objects.create(
            catmat='654324', descricao='Milho', unidade_medida='KG', categoria='SM',
        )
        estoque = Estoque.objects.get(item_generico=genero)
        self.assertEqual(estoque.saldo_atual, Decimal('0.000'))
        self.assertFalse(LoteEstoque.objects.filter(estoque=estoque).exists())

    def test_carga_inicial_real_e_producao_preservam_invariante(self):
        carga = self.registrar_carga_teste('100', numero='INICIAL-FLUXO')
        saida = registrar_saida(
            item_generico_id=self.genero.id,
            quantidade='35',
            tipo_saida='PRODUCAO',
            justificativa='Produção do almoço',
            usuario=self.estoquista,
        )
        estoque = Estoque.objects.get(item_generico=self.genero)
        lote = LoteEstoque.objects.get(estoque=estoque, numero_lote='INICIAL-FLUXO')
        self.assertEqual(estoque.saldo_atual, Decimal('65.000'))
        self.assertEqual(lote.saldo_atual, Decimal('65.000'))
        self.assertFalse(LoteEstoque.objects.filter(estoque=estoque, legado=True).exists())
        self.assertEqual(carga.alocacoes_lote.get().lote, lote)
        self.assertEqual(saida.alocacoes_lote.get().lote, lote)

    def test_recebimento_registra_lote_real_e_alocacao_explicita(self):
        _, movimentos = registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'lotes': [self.lote_recebimento('500')],
            }],
            usuario=self.estoquista,
        )
        movimento = movimentos[0]
        estoque = Estoque.objects.get(item_generico=self.genero)
        lote = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-TESTE-001')
        self.assertEqual(estoque.saldo_atual, Decimal('500.000'))
        self.assertEqual(lote.saldo_atual, Decimal('500.000'))
        self.assertFalse(LoteEstoque.objects.filter(estoque=estoque, legado=True).exists())
        self.assertEqual(movimento.alocacoes_lote.get().lote, lote)

    def test_estorno_da_carga_inicial_restaura_lote_real(self):
        original = self.registrar_carga_teste('25', numero='INICIAL-ESTORNO')
        estorno = estornar_movimentacao(
            movimentacao_id=original.id,
            justificativa='Lançamento incorreto',
            usuario=self.estoquista,
        )
        estoque = Estoque.objects.get(item_generico=self.genero)
        lote = LoteEstoque.objects.get(estoque=estoque, numero_lote='INICIAL-ESTORNO')
        self.assertEqual(estoque.saldo_atual, Decimal('0.000'))
        self.assertEqual(lote.saldo_atual, Decimal('0.000'))
        self.assertEqual(original.alocacoes_lote.get().lote, lote)
        self.assertEqual(estorno.alocacoes_lote.get().lote, lote)

    def test_ajuste_atual_preserva_saldo_por_lote(self):
        carga = self.registrar_carga_teste('50', numero='INICIAL-AJUSTE')
        lote = carga.alocacoes_lote.get().lote
        item, movimentos = registrar_ajuste(
            item_generico_id=self.genero.id,
            lotes=[{'lote_id': lote.id, 'quantidade_contada': '47'}],
            justificativa='Contagem mensal',
            usuario=self.estoquista,
        )
        estoque = Estoque.objects.get(item_generico=self.genero)
        lote.refresh_from_db()
        self.assertEqual(estoque.saldo_atual, Decimal('47.000'))
        self.assertEqual(lote.saldo_atual, Decimal('47.000'))
        self.assertEqual(len(movimentos), 1)
        self.assertEqual(movimentos[0].item_inventario_id, item.id)

    def test_movimentacao_lote_rejeita_lote_de_outro_estoque(self):
        movimento = self.registrar_carga_teste('10', numero='INICIAL-ORIGEM')
        outro_genero = ItemGenerico.objects.create(
            catmat='654323', descricao='Feijão', unidade_medida='KG', categoria='SM',
        )
        outro_estoque = Estoque.objects.get(item_generico=outro_genero)
        lote_outro_estoque = LoteEstoque.objects.create(
            estoque=outro_estoque,
            numero_lote='OUTRO-LOTE',
            data_validade=date(2099, 12, 31),
            saldo_atual=Decimal('0.000'),
            legado=False,
        )
        with self.assertRaises(DjangoValidationError):
            MovimentacaoLote.objects.create(
                movimentacao=movimento,
                lote=lote_outro_estoque,
                quantidade=Decimal('1.000'),
                saldo_lote_resultante=Decimal('0.000'),
            )


class HardeningEstoqueTests(EstoqueBaseMixin, TestCase):
    def setUp(self):
        self.criar_cenario()

    def test_fluxo_integrado_por_lotes_preserva_todas_as_invariantes(self):
        registrar_carga_inicial(
            item_generico_id=self.genero.id,
            lotes=[
                self.lote_recebimento('50', numero='INTEGRADO-A', validade='2099-01-01'),
                self.lote_recebimento('50', numero='INTEGRADO-B', validade='2099-02-01'),
            ],
            justificativa='Carga inicial integrada.',
            usuario=self.estoquista,
        )
        estoque = Estoque.objects.get(item_generico=self.genero)
        self.assert_integridade_estoque(estoque)

        saida = registrar_saida(
            item_generico_id=self.genero.id,
            quantidade='60',
            tipo_saida='PRODUCAO',
            justificativa='Produção integrada.',
            usuario=self.estoquista,
        )
        self.assert_integridade_estoque(estoque)

        lote_b = LoteEstoque.objects.get(estoque=estoque, numero_lote='INTEGRADO-B')
        registrar_saida(
            item_generico_id=self.genero.id,
            quantidade='5',
            tipo_saida='PERDA',
            lote_id=lote_b.id,
            justificativa='Perda integrada.',
            usuario=self.estoquista,
        )
        self.assert_integridade_estoque(estoque)

        registrar_ajuste(
            item_generico_id=self.genero.id,
            lotes=[
                {'lote_id': lote_b.id, 'quantidade_contada': '30'},
                {
                    'numero_lote': 'INTEGRADO-C',
                    'data_validade': '2099-03-01',
                    'quantidade_contada': '15',
                },
            ],
            justificativa='Inventário integrado.',
            usuario=self.estoquista,
        )
        self.assert_integridade_estoque(estoque)

        estornar_movimentacao(
            movimentacao_id=saida.id,
            justificativa='Estorno integrado.',
            usuario=self.estoquista,
        )
        self.assert_integridade_estoque(estoque)

    def test_saldos_utilizaveis_em_lote_e_bulk_sao_equivalentes(self):
        referencia = date(2026, 10, 30)
        self.lote_estoque('BULK-VENCIDO', '30', referencia - timedelta(days=1))
        self.lote_estoque('BULK-VALIDO', '50', referencia)
        self.lote_estoque('LEGADO', '20', legado=True)
        estoque_principal = Estoque.objects.get(item_generico=self.genero)

        outro_genero = ItemGenerico.objects.create(
            catmat='654322', descricao='Macarrão', unidade_medida='KG', categoria='SM',
        )
        outro_estoque = Estoque.objects.get(item_generico=outro_genero)
        LoteEstoque.objects.create(
            estoque=outro_estoque,
            numero_lote='BULK-OUTRO-VENCIDO',
            data_validade=referencia - timedelta(days=1),
            saldo_atual=Decimal('10.000'),
            legado=False,
        )
        LoteEstoque.objects.create(
            estoque=outro_estoque,
            numero_lote='BULK-OUTRO-HOJE',
            data_validade=referencia,
            saldo_atual=Decimal('25.000'),
            legado=False,
        )
        Estoque.objects.filter(pk=outro_estoque.pk).update(saldo_atual=Decimal('35.000'))

        saldos_bulk = saldos_utilizaveis_por_estoque(
            [estoque_principal.id, outro_estoque.id],
            referencia,
        )

        self.assertEqual(
            saldos_bulk.get(estoque_principal.id, Decimal('0.000')),
            saldo_utilizavel_estoque(estoque_principal, referencia),
        )
        self.assertEqual(
            saldos_bulk.get(outro_estoque.id, Decimal('0.000')),
            saldo_utilizavel_estoque(outro_estoque, referencia),
        )

    def test_listagem_estoque_preserva_saldo_utilizavel_com_prefetch(self):
        hoje = data_atual_estoque()
        self.lote_estoque('PREFETCH-VENCIDO', '30', hoje - timedelta(days=1))
        self.lote_estoque('PREFETCH-VALIDO', '50', hoje)
        self.lote_estoque('LEGADO', '20', legado=True)

        outro_genero = ItemGenerico.objects.create(
            catmat='654321', descricao='Arroz integral', unidade_medida='KG', categoria='SM',
        )
        outro_estoque = Estoque.objects.get(item_generico=outro_genero)
        LoteEstoque.objects.create(
            estoque=outro_estoque,
            numero_lote='PREFETCH-OUTRO-VENCIDO',
            data_validade=hoje - timedelta(days=1),
            saldo_atual=Decimal('10.000'),
            legado=False,
        )
        LoteEstoque.objects.create(
            estoque=outro_estoque,
            numero_lote='PREFETCH-OUTRO-VALIDO',
            data_validade=hoje + timedelta(days=1),
            saldo_atual=Decimal('40.000'),
            legado=False,
        )
        Estoque.objects.filter(pk=outro_estoque.pk).update(saldo_atual=Decimal('50.000'))

        cliente = APIClient()
        cliente.force_authenticate(self.diretor)
        resposta = cliente.get(reverse('estoque-list'), {'page_size': 100})
        self.assertEqual(resposta.status_code, 200, resposta.data)
        por_genero = {linha['item_generico_id']: linha for linha in resposta.data['results']}
        self.assertEqual(Decimal(por_genero[self.genero.id]['saldo_utilizavel']), Decimal('70.000'))
        self.assertEqual(Decimal(por_genero[outro_genero.id]['saldo_utilizavel']), Decimal('40.000'))


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
        self.registrar_carga_teste(
            item_generico_id=self.genero.id, quantidade='50', justificativa='Implantação',
            usuario=self.estoquista,
        )
        self.client.force_authenticate(self.estoquista)

    def inventariar(self, quantidade_contada):
        lote = LoteEstoque.objects.get(
            estoque__item_generico=self.genero,
            legado=False,
        )
        return self.client.post(reverse('estoque-ajustes'), {
            'item_generico_id': self.genero.id,
            'lotes': [{
                'lote_id': lote.id,
                'quantidade_contada': quantidade_contada,
            }],
            'justificativa': 'Contagem mensal',
        }, format='json')

    def test_contagem_menor_lanca_falta_pela_diferenca(self):
        resposta = self.inventariar('47')
        self.assertEqual(resposta.status_code, 201, resposta.data)
        movimento = resposta.data[0]
        self.assertEqual(movimento['tipo'], MovimentacaoEstoque.Tipo.AJUSTE_NEGATIVO)
        self.assertEqual(movimento['tipo_descricao'], 'Inventário (falta)')
        self.assertEqual(Decimal(movimento['quantidade']), Decimal('3'))
        self.assertEqual(Estoque.objects.get(item_generico=self.genero).saldo_atual, Decimal('47.000'))

    def test_contagem_maior_lanca_sobra(self):
        resposta = self.inventariar('52.5')
        self.assertEqual(resposta.status_code, 201, resposta.data)
        self.assertEqual(resposta.data[0]['tipo'], MovimentacaoEstoque.Tipo.AJUSTE_POSITIVO)
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


class InventarioPorLoteTests(EstoqueBaseMixin, APITestCase):
    def setUp(self):
        self.criar_cenario()
        self.client.force_authenticate(self.estoquista)

    def carga(self, lotes, **kwargs):
        return registrar_carga_inicial(
            item_generico_id=self.genero.id,
            lotes=lotes,
            justificativa='Implantação por lote',
            usuario=self.estoquista,
            **kwargs,
        )

    def inventariar(self, lotes):
        return registrar_ajuste(
            item_generico_id=self.genero.id,
            lotes=lotes,
            justificativa='Contagem física por lote',
            usuario=self.estoquista,
        )

    def test_carga_inicial_registra_lotes_reais(self):
        movimento = self.carga([
            self.lote_recebimento('30', numero='INICIAL-A'),
            self.lote_recebimento('20', numero='INICIAL-B'),
        ])
        estoque = Estoque.objects.get(item_generico=self.genero)
        self.assertEqual(estoque.saldo_atual, Decimal('50.000'))
        self.assertEqual(movimento.quantidade, Decimal('50.000'))
        self.assertEqual(movimento.alocacoes_lote.count(), 2)
        self.assertFalse(LoteEstoque.objects.filter(estoque=estoque, legado=True).exists())
        self.assertEqual(
            set(LoteEstoque.objects.filter(estoque=estoque).values_list('numero_lote', 'saldo_atual')),
            {('INICIAL-A', Decimal('30.000')), ('INICIAL-B', Decimal('20.000'))},
        )

    def test_carga_inicial_cria_contagens(self):
        movimento = self.carga([
            self.lote_recebimento('30', numero='INICIAL-A'),
            self.lote_recebimento('20', numero='INICIAL-B'),
        ])
        item = movimento.item_inventario
        self.assertEqual(item.saldo_sistema, Decimal('0.000'))
        self.assertEqual(item.quantidade_contada, Decimal('50.000'))
        self.assertEqual(
            set(item.contagens_lote.values_list('saldo_sistema', 'quantidade_contada')),
            {(Decimal('0.000'), Decimal('30.000')), (Decimal('0.000'), Decimal('20.000'))},
        )

    def test_carga_inicial_nao_aceita_legado(self):
        with self.assertRaises(ValidationError):
            self.carga([self.lote_recebimento('10', numero='LEGADO')])
        self.assertFalse(MovimentacaoEstoque.objects.exists())
        self.assertEqual(Estoque.objects.get(item_generico=self.genero).saldo_atual, Decimal('0.000'))

    def test_carga_inicial_somente_estoque_zero_e_uma_vez(self):
        registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'lotes': [self.lote_recebimento('10', numero='RECEBIDO')],
                'observacao': 'Saldo restante pendente.',
            }],
            usuario=self.estoquista,
        )
        with self.assertRaises(ValidationError):
            self.carga([self.lote_recebimento('10', numero='INICIAL-APOS-RECEBIMENTO')])

        outro_genero = ItemGenerico.objects.create(
            catmat='654350', descricao='Lentilha', unidade_medida='KG', categoria='SM',
        )
        registrar_carga_inicial(
            item_generico_id=outro_genero.id,
            lotes=[self.lote_recebimento('10', numero='UNICA-CARGA')],
            justificativa='Implantação',
            usuario=self.estoquista,
        )
        estoque_outro = Estoque.objects.get(item_generico=outro_genero)
        Estoque.objects.filter(pk=estoque_outro.pk).update(saldo_atual=Decimal('0.000'))
        LoteEstoque.objects.filter(estoque=estoque_outro).update(saldo_atual=Decimal('0.000'))
        with self.assertRaises(ValidationError):
            registrar_carga_inicial(
                item_generico_id=outro_genero.id,
                lotes=[self.lote_recebimento('1', numero='SEGUNDA-CARGA')],
                justificativa='Outra implantação',
                usuario=self.estoquista,
            )

    def test_carga_inicial_aceita_lote_vencido_como_saldo_fisico(self):
        momento = datetime(2026, 10, 30, 12, tzinfo=dt_timezone.utc)
        self.carga([
            self.lote_recebimento('10', numero='INICIAL-VENCIDO', validade='2026-10-29'),
        ], data_hora=momento)
        estoque = Estoque.objects.get(item_generico=self.genero)
        self.assertEqual(estoque.saldo_atual, Decimal('10.000'))
        self.assertEqual(saldo_utilizavel_estoque(estoque, date(2026, 10, 30)), Decimal('0.000'))

    def test_inventario_diminui_e_aumenta_lotes_individualmente(self):
        self.carga([
            self.lote_recebimento('50', numero='LOTE-A'),
            self.lote_recebimento('20', numero='LOTE-B'),
        ])
        estoque = Estoque.objects.get(item_generico=self.genero)
        lote_a = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-A')
        lote_b = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-B')
        item, movimentos = self.inventariar([
            {'lote_id': lote_a.id, 'quantidade_contada': '47'},
            {'lote_id': lote_b.id, 'quantidade_contada': '25'},
        ])
        lote_a.refresh_from_db()
        lote_b.refresh_from_db()
        self.assertEqual(lote_a.saldo_atual, Decimal('47.000'))
        self.assertEqual(lote_b.saldo_atual, Decimal('25.000'))
        self.assertEqual(len(movimentos), 2)
        self.assertEqual({movimento.tipo for movimento in movimentos}, {
            MovimentacaoEstoque.Tipo.AJUSTE_NEGATIVO,
            MovimentacaoEstoque.Tipo.AJUSTE_POSITIVO,
        })
        self.assertTrue(all(movimento.item_inventario_id == item.id for movimento in movimentos))

    def test_inventario_redistribui_sem_alterar_total(self):
        self.carga([
            self.lote_recebimento('30', numero='LOTE-A'),
            self.lote_recebimento('20', numero='LOTE-B'),
        ])
        estoque = Estoque.objects.get(item_generico=self.genero)
        lote_a = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-A')
        lote_b = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-B')
        item, movimentos = self.inventariar([
            {'lote_id': lote_a.id, 'quantidade_contada': '20'},
            {'lote_id': lote_b.id, 'quantidade_contada': '30'},
        ])
        estoque.refresh_from_db()
        self.assertEqual(estoque.saldo_atual, Decimal('50.000'))
        self.assertEqual(len(movimentos), 2)
        self.assertEqual(item.movimentacoes_estoque.count(), 2)

    def test_ajustes_de_inventario_nao_podem_ser_estornados_individualmente(self):
        self.carga([
            self.lote_recebimento('30', numero='LOTE-A'),
            self.lote_recebimento('20', numero='LOTE-B'),
        ])
        estoque = Estoque.objects.get(item_generico=self.genero)
        lote_a = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-A')
        lote_b = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-B')
        _, movimentos = self.inventariar([
            {'lote_id': lote_a.id, 'quantidade_contada': '20'},
            {'lote_id': lote_b.id, 'quantidade_contada': '30'},
        ])
        saldos_antes = {
            lote.id: lote.saldo_atual
            for lote in LoteEstoque.objects.filter(estoque=estoque)
        }

        for movimento in movimentos:
            with self.subTest(tipo=movimento.tipo), self.assertRaises(ValidationError) as erro:
                estornar_movimentacao(
                    movimentacao_id=movimento.id,
                    justificativa='Correção indevida de inventário.',
                    usuario=self.estoquista,
                )
            self.assertIn('nova contagem', str(erro.exception).lower())

        self.assertFalse(MovimentacaoEstoque.objects.filter(
            tipo=MovimentacaoEstoque.Tipo.ESTORNO,
        ).exists())
        self.assertEqual(
            {
                lote.id: lote.saldo_atual
                for lote in LoteEstoque.objects.filter(estoque=estoque)
            },
            saldos_antes,
        )
        self.assert_integridade_estoque(estoque)

    def test_inventario_regulariza_legado_e_descobre_lote(self):
        lote_legado = self.lote_estoque('LEGADO', '50', legado=True)
        item, movimentos = self.inventariar([
            {'lote_id': lote_legado.id, 'quantidade_contada': '0'},
            {'numero_lote': 'LOTE-A', 'data_validade': '2099-12-31', 'quantidade_contada': '30'},
            {'numero_lote': 'LOTE-B', 'data_validade': '2099-11-30', 'quantidade_contada': '20'},
        ])
        estoque = Estoque.objects.get(item_generico=self.genero)
        lote_legado.refresh_from_db()
        self.assertEqual(lote_legado.saldo_atual, Decimal('0.000'))
        self.assertEqual(estoque.saldo_atual, Decimal('50.000'))
        self.assertEqual(len(movimentos), 2)
        self.assertEqual(item.quantidade_contada, Decimal('50.000'))
        self.assertEqual(item.contagens_lote.count(), 3)

    def test_inventario_reutiliza_lote_zerado_e_rejeita_validade_divergente(self):
        estoque = Estoque.objects.get(item_generico=self.genero)
        lote = LoteEstoque.objects.create(
            estoque=estoque,
            numero_lote='ABC',
            data_validade=date(2099, 12, 31),
            saldo_atual=Decimal('0.000'),
            legado=False,
        )
        self.inventariar([
            {'numero_lote': 'abc', 'data_validade': '2099-12-31', 'quantidade_contada': '10'},
        ])
        lote.refresh_from_db()
        self.assertEqual(lote.saldo_atual, Decimal('10.000'))
        with self.assertRaises(ValidationError):
            self.inventariar([
                {'lote_id': lote.id, 'quantidade_contada': '10'},
                {'numero_lote': 'ABC', 'data_validade': '2099-11-30', 'quantidade_contada': '1'},
            ])

    def test_inventario_exige_todos_os_lotes_positivos_e_permite_zerar(self):
        self.carga([
            self.lote_recebimento('20', numero='LOTE-A'),
            self.lote_recebimento('30', numero='LOTE-B'),
        ])
        estoque = Estoque.objects.get(item_generico=self.genero)
        lote_a = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-A')
        lote_b = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-B')
        with self.assertRaises(ValidationError):
            self.inventariar([{'lote_id': lote_a.id, 'quantidade_contada': '20'}])
        _, movimentos = self.inventariar([
            {'lote_id': lote_a.id, 'quantidade_contada': '0'},
            {'lote_id': lote_b.id, 'quantidade_contada': '30'},
        ])
        lote_a.refresh_from_db()
        self.assertEqual(lote_a.saldo_atual, Decimal('0.000'))
        self.assertEqual(len(movimentos), 1)

    def test_inventario_igual_reverte_sem_historico_e_preserva_snapshots(self):
        self.carga([
            self.lote_recebimento('20', numero='LOTE-A'),
            self.lote_recebimento('30', numero='LOTE-B'),
        ])
        estoque = Estoque.objects.get(item_generico=self.genero)
        lote_a = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-A')
        lote_b = LoteEstoque.objects.get(estoque=estoque, numero_lote='LOTE-B')
        inventarios_antes = Inventario.objects.count()
        with self.assertRaises(ValidationError):
            self.inventariar([
                {'lote_id': lote_a.id, 'quantidade_contada': '20'},
                {'lote_id': lote_b.id, 'quantidade_contada': '30'},
            ])
        self.assertEqual(Inventario.objects.count(), inventarios_antes)
        item, _ = self.inventariar([
            {'lote_id': lote_a.id, 'quantidade_contada': '18'},
            {'lote_id': lote_b.id, 'quantidade_contada': '35'},
        ])
        self.assertEqual(
            set(item.contagens_lote.values_list('saldo_sistema', 'quantidade_contada')),
            {(Decimal('20.000'), Decimal('18.000')), (Decimal('30.000'), Decimal('35.000'))},
        )

    def test_endpoint_lotes_para_inventario_e_ajuste_http_com_dois_movimentos(self):
        vencido = self.lote_estoque('VENCIDO', '5', date(2026, 1, 1))
        valido = self.lote_estoque('VALIDO', '10', date(2099, 12, 31))
        legado = self.lote_estoque('LEGADO', '3', legado=True)
        LoteEstoque.objects.create(
            estoque=Estoque.objects.get(item_generico=self.genero),
            numero_lote='ZERADO',
            data_validade=date(2099, 12, 31),
            saldo_atual=Decimal('0.000'),
            legado=False,
        )
        resposta = self.client.get(
            reverse('estoque-lotes-para-inventario'),
            {'item_generico_id': self.genero.id},
        )
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual([item['id'] for item in resposta.data], [legado.id, vencido.id, valido.id])
        resposta = self.client.post(reverse('estoque-ajustes'), {
            'item_generico_id': self.genero.id,
            'lotes': [
                {'lote_id': legado.id, 'quantidade_contada': '2'},
                {'lote_id': vencido.id, 'quantidade_contada': '6'},
                {'lote_id': valido.id, 'quantidade_contada': '10'},
            ],
            'justificativa': 'Redistribuição por inventário',
        }, format='json')
        self.assertEqual(resposta.status_code, 201, resposta.data)
        self.assertEqual(len(resposta.data), 2)


class LotesValidadeTests(EstoqueBaseMixin, APITestCase):
    def setUp(self):
        self.criar_cenario()
        self.client.force_authenticate(self.diretor)

    def _resultados(self, resposta):
        return resposta.data['results']

    def test_status_lote_validade_respeita_faixas(self):
        referencia = date(2026, 10, 30)
        faixas = (
            ('VENCIDO', date(2026, 10, 29), -1),
            ('VENCE_HOJE', date(2026, 10, 30), 0),
            ('CRITICO', date(2026, 10, 31), 1),
            ('CRITICO', date(2026, 11, 6), 7),
            ('ATENCAO', date(2026, 11, 7), 8),
            ('ATENCAO', date(2026, 11, 29), 30),
            ('REGULAR', date(2026, 11, 30), 31),
        )
        for indice, (status, validade, dias) in enumerate(faixas, start=1):
            with self.subTest(status=status, validade=validade):
                lote = self.lote_estoque(f'FAIXA-{indice}', '1', validade)
                self.assertEqual(dias_para_validade(lote, referencia), dias)
                self.assertEqual(status_lote_validade(lote, referencia), status)

        legado = self.lote_estoque('LEGADO', '1', legado=True)
        self.assertIsNone(dias_para_validade(legado, referencia))
        self.assertEqual(status_lote_validade(legado, referencia), 'SEM_VALIDADE')

    def test_helpers_genericos_de_validade_respeitam_limites(self):
        referencia = date(2026, 10, 30)
        faixas = (
            (date(2026, 10, 29), -1, 'VENCIDO'),
            (date(2026, 10, 30), 0, 'VENCE_HOJE'),
            (date(2026, 11, 6), 7, 'CRITICO'),
            (date(2026, 11, 7), 8, 'ATENCAO'),
            (date(2026, 11, 29), 30, 'ATENCAO'),
            (date(2026, 11, 30), 31, 'REGULAR'),
        )

        for validade, dias, status in faixas:
            with self.subTest(validade=validade):
                self.assertEqual(dias_para_data_validade(validade, referencia), dias)
                self.assertEqual(status_data_validade(validade, referencia), status)

        self.assertIsNone(dias_para_data_validade(None, referencia))
        self.assertEqual(status_data_validade(None, referencia), 'SEM_VALIDADE')

    def test_lote_validade_serializer_expoe_campos_calculados(self):
        lote = self.lote_estoque('SERIAL-001', '12.5', date(2099, 12, 31))
        dados = LoteValidadeSerializer(lote).data

        self.assertEqual(dados['descricao'], self.genero.descricao)
        self.assertEqual(dados['catmat'], self.genero.catmat)
        self.assertEqual(dados['unidade_medida'], self.genero.unidade_medida)
        self.assertEqual(dados['numero_lote'], 'SERIAL-001')
        self.assertEqual(Decimal(dados['saldo_atual']), Decimal('12.500'))
        self.assertEqual(dados['data_validade'], '2099-12-31')
        self.assertEqual(dados['dias_para_validade'], dias_para_validade(lote))
        self.assertEqual(dados['status'], status_lote_validade(lote))
        self.assertEqual(dados['status_descricao'], STATUS_VALIDADE_DESCRICOES[dados['status']])

    def test_listagem_exclui_lotes_zerados_e_aceita_saldo_positivo_false(self):
        lote_positivo = self.lote_estoque('POSITIVO', '10', date(2099, 12, 31))
        lote_zerado = self.lote_estoque('ZERADO', '0', date(2099, 12, 31))

        resposta = self.client.get(reverse('lote-estoque-list'))
        self.assertEqual(resposta.status_code, 200, resposta.data)
        ids = {item['id'] for item in self._resultados(resposta)}
        self.assertIn(lote_positivo.id, ids)
        self.assertNotIn(lote_zerado.id, ids)

        resposta = self.client.get(reverse('lote-estoque-list'), {'saldo_positivo': 'false'})
        self.assertEqual(resposta.status_code, 200, resposta.data)
        ids = {item['id'] for item in self._resultados(resposta)}
        self.assertEqual(ids, {lote_positivo.id, lote_zerado.id})

    def test_listagem_ordena_e_filtra_status_de_validade(self):
        hoje = timezone.localtime(timezone.now(), FUSO_ESTOQUE).date()
        vencido = self.lote_estoque('VENCIDO', '1', hoje - timedelta(days=1))
        vence_hoje = self.lote_estoque('HOJE', '1', hoje)
        critico = self.lote_estoque('CRITICO', '1', hoje + timedelta(days=1))
        atencao = self.lote_estoque('ATENCAO', '1', hoje + timedelta(days=8))
        regular = self.lote_estoque('REGULAR', '1', hoje + timedelta(days=31))
        legado = self.lote_estoque('LEGADO', '1', legado=True)

        resposta = self.client.get(reverse('lote-estoque-list'))
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(
            [item['id'] for item in self._resultados(resposta)],
            [vencido.id, vence_hoje.id, critico.id, atencao.id, regular.id, legado.id],
        )

        esperados = {
            'VENCIDO': {vencido.id},
            'CRITICO': {critico.id},
            'ATENCAO': {atencao.id},
            'SEM_VALIDADE': {legado.id},
        }
        for status, ids_esperados in esperados.items():
            with self.subTest(status=status):
                resposta = self.client.get(reverse('lote-estoque-list'), {'status': status})
                self.assertEqual(resposta.status_code, 200, resposta.data)
                self.assertEqual(
                    {item['id'] for item in self._resultados(resposta)},
                    ids_esperados,
                )

    def test_listagem_rejeita_status_invalido(self):
        resposta = self.client.get(reverse('lote-estoque-list'), {'status': 'QUALQUER_COISA'})
        self.assertEqual(resposta.status_code, 400)

    def test_listagem_busca_categoria_e_periodo_de_validade(self):
        hoje = timezone.localtime(timezone.now(), FUSO_ESTOQUE).date()
        lote_principal = self.lote_estoque('ABC123', '10', hoje + timedelta(days=10))
        outro_genero = ItemGenerico.objects.create(
            catmat='654322', descricao='Feijao branco', unidade_medida='KG', categoria='NP',
        )
        outro_estoque = Estoque.objects.get(item_generico=outro_genero)
        lote_outro = LoteEstoque.objects.create(
            estoque=outro_estoque,
            numero_lote='OUTRO-001',
            data_validade=hoje + timedelta(days=20),
            saldo_atual=Decimal('10.000'),
            legado=False,
        )

        for busca, ids_esperados in (
            ('ABC123', {lote_principal.id}),
            (self.genero.descricao, {lote_principal.id}),
        ):
            with self.subTest(busca=busca):
                resposta = self.client.get(reverse('lote-estoque-list'), {'search': busca})
                self.assertEqual(resposta.status_code, 200, resposta.data)
                self.assertEqual(
                    {item['id'] for item in self._resultados(resposta)},
                    ids_esperados,
                )

        resposta = self.client.get(reverse('lote-estoque-list'), {'categoria': 'NP'})
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual({item['id'] for item in self._resultados(resposta)}, {lote_outro.id})

        resposta = self.client.get(reverse('lote-estoque-list'), {
            'data_validade__gte': (hoje + timedelta(days=9)).isoformat(),
            'data_validade__lte': (hoje + timedelta(days=11)).isoformat(),
        })
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual({item['id'] for item in self._resultados(resposta)}, {lote_principal.id})

    def test_resumo_conta_somente_lotes_positivos_por_status(self):
        hoje = timezone.localtime(timezone.now(), FUSO_ESTOQUE).date()
        self.lote_estoque('VENCIDO', '1', hoje - timedelta(days=1))
        self.lote_estoque('HOJE', '1', hoje)
        self.lote_estoque('CRITICO', '1', hoje + timedelta(days=1))
        self.lote_estoque('ATENCAO', '1', hoje + timedelta(days=8))
        self.lote_estoque('REGULAR', '1', hoje + timedelta(days=31))
        self.lote_estoque('LEGADO', '1', legado=True)
        self.lote_estoque('ZERADO', '0', hoje + timedelta(days=2))

        resposta = self.client.get(reverse('lote-estoque-resumo'))
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.data, {
            'total_lotes': 6,
            'vencidos': 1,
            'vence_hoje': 1,
            'criticos': 1,
            'atencao': 1,
            'regulares': 1,
            'sem_validade': 1,
        })

    def test_consulta_lotes_validades_usa_permissao_estoque_consultar(self):
        usuarios = (self.diretor, self.tecnico, self.nutricionista, self.estoquista)
        for usuario in usuarios:
            with self.subTest(usuario=usuario.papel):
                self.client.force_authenticate(usuario)
                resposta = self.client.get(reverse('lote-estoque-list'))
                self.assertEqual(resposta.status_code, 200, resposta.data)


class IndicadoresValidadeEstoqueTests(EstoqueBaseMixin, APITestCase):
    def setUp(self):
        self.criar_cenario()
        self.client.force_authenticate(self.diretor)

    def _listar_na_referencia(self, referencia):
        with patch(
            'estoque.views.data_atual_estoque', return_value=referencia
        ), patch(
            'utils.estoque_services.data_atual_estoque', return_value=referencia
        ):
            return self.client.get(reverse('estoque-list'), {'page_size': 100})

    def _dados_do_genero(self, resposta):
        return next(
            item
            for item in resposta.data['results']
            if item['item_generico_id'] == self.genero.id
        )

    def test_listagem_estoque_informa_resumo_de_validade_por_genero(self):
        referencia = date(2026, 10, 30)
        self.lote_estoque('IND-VENCIDO', '10', referencia - timedelta(days=1))
        self.lote_estoque('IND-HOJE', '10', referencia)
        self.lote_estoque('IND-CRITICO', '10', referencia + timedelta(days=3))
        self.lote_estoque('IND-ATENCAO', '10', referencia + timedelta(days=15))
        self.lote_estoque('IND-REGULAR', '10', referencia + timedelta(days=60))
        self.lote_estoque('IND-LEGADO', '10', legado=True)
        self.lote_estoque('IND-ZERO-VENCIDO', '0', referencia - timedelta(days=2))
        self.lote_estoque('IND-ZERO-CRITICO', '0', referencia + timedelta(days=2))

        resposta = self._listar_na_referencia(referencia)

        self.assertEqual(resposta.status_code, 200, resposta.data)
        dados = self._dados_do_genero(resposta)
        self.assertEqual(dados['lotes_vencidos'], 1)
        self.assertEqual(dados['lotes_vence_hoje'], 1)
        self.assertEqual(dados['lotes_criticos'], 1)
        self.assertEqual(dados['lotes_atencao'], 1)
        self.assertEqual(dados['proxima_validade'], referencia.isoformat())
        self.assertEqual(dados['dias_para_proxima_validade'], 0)
        self.assertEqual(dados['status_proxima_validade'], 'VENCE_HOJE')
        self.assertEqual(
            dados['status_proxima_validade_descricao'],
            STATUS_VALIDADE_DESCRICOES['VENCE_HOJE'],
        )

    def test_listagem_estoque_ignora_vencido_na_proxima_validade(self):
        referencia = date(2026, 10, 30)
        self.lote_estoque('PROX-VENCIDO', '10', referencia - timedelta(days=1))
        self.lote_estoque('PROX-CRITICO', '10', referencia + timedelta(days=5))
        self.lote_estoque('PROX-ATENCAO', '10', referencia + timedelta(days=20))

        resposta = self._listar_na_referencia(referencia)

        self.assertEqual(resposta.status_code, 200, resposta.data)
        dados = self._dados_do_genero(resposta)
        self.assertEqual(dados['lotes_vencidos'], 1)
        self.assertEqual(dados['proxima_validade'], (referencia + timedelta(days=5)).isoformat())
        self.assertEqual(dados['dias_para_proxima_validade'], 5)
        self.assertEqual(dados['status_proxima_validade'], 'CRITICO')

    def test_listagem_estoque_sem_proxima_validade_utilizavel(self):
        referencia = date(2026, 10, 30)
        self.lote_estoque('SEM-PROXIMA-VENCIDO', '10', referencia - timedelta(days=1))
        self.lote_estoque('LEGADO', '10', legado=True)

        resposta = self._listar_na_referencia(referencia)

        self.assertEqual(resposta.status_code, 200, resposta.data)
        dados = self._dados_do_genero(resposta)
        self.assertGreater(dados['lotes_vencidos'], 0)
        self.assertIsNone(dados['proxima_validade'])
        self.assertIsNone(dados['dias_para_proxima_validade'])
        self.assertIsNone(dados['status_proxima_validade'])
        self.assertIsNone(dados['status_proxima_validade_descricao'])


class ExtratoPorLoteTests(EstoqueBaseMixin, APITestCase):
    def setUp(self):
        self.criar_cenario()
        self.client.force_authenticate(self.diretor)

    def receber(self, lotes):
        total = sum(Decimal(str(lote['quantidade'])) for lote in lotes)
        _, movimentos = registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id,
                'lotes': lotes,
                'observacao': 'Entrega parcial para teste de rastreabilidade.' if total < 500 else '',
            }],
            usuario=self.estoquista,
        )
        return movimentos[0]

    def resposta_rastreabilidade(self, lote):
        return self.client.get(
            reverse('movimentacao-estoque-rastreabilidade-lote'),
            {'lote_id': lote.id},
        )

    def test_extrato_expoe_alocacoes_sem_duplicar_movimento(self):
        movimento = self.receber([self.lote_recebimento('500', numero='EXTRATO-A')])

        resposta = self.client.get(reverse('movimentacao-estoque-list'))
        self.assertEqual(resposta.status_code, 200, resposta.data)
        movimentos = [item for item in resposta.data['results'] if item['id'] == movimento.id]
        self.assertEqual(len(movimentos), 1)
        alocacoes = movimentos[0]['alocacoes_lote']
        self.assertEqual(len(alocacoes), 1)
        self.assertEqual(alocacoes[0]['numero_lote'], 'EXTRATO-A')
        self.assertEqual(Decimal(alocacoes[0]['quantidade']), Decimal('500.000'))
        self.assertEqual(Decimal(alocacoes[0]['saldo_lote_resultante']), Decimal('500.000'))

    def test_extrato_mantem_uma_linha_com_duas_alocacoes(self):
        self.receber([
            self.lote_recebimento('200', numero='EXTRATO-A'),
            self.lote_recebimento('300', numero='EXTRATO-B'),
        ])
        saida = registrar_saida(
            item_generico_id=self.genero.id,
            quantidade='250',
            tipo_saida='PRODUCAO',
            justificativa='Teste de FEFO para extrato',
            usuario=self.estoquista,
        )

        resposta = self.client.get(reverse('movimentacao-estoque-list'))
        self.assertEqual(resposta.status_code, 200, resposta.data)
        movimentos = [item for item in resposta.data['results'] if item['id'] == saida.id]
        self.assertEqual(len(movimentos), 1)
        self.assertEqual(len(movimentos[0]['alocacoes_lote']), 2)

    def test_extrato_filtra_por_lote_e_rejeita_lote_invalido(self):
        carga = self.registrar_carga_teste('100', numero='FILTRO-A')
        lote_a = LoteEstoque.objects.get(estoque__item_generico=self.genero, numero_lote='FILTRO-A')
        registrar_saida(
            item_generico_id=self.genero.id,
            quantidade='10',
            tipo_saida='PERDA',
            lote_id=lote_a.id,
            justificativa='Perda do lote A',
            usuario=self.estoquista,
        )

        resposta = self.client.get(reverse('movimentacao-estoque-list'), {'lote_id': lote_a.id})
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual({item['id'] for item in resposta.data['results']}, {
            carga.id,
            MovimentacaoEstoque.objects.filter(
                estoque__item_generico=self.genero,
                tipo=MovimentacaoEstoque.Tipo.SAIDA_PERDA,
            ).get().id,
        })
        for lote_id in ('abc', '0'):
            with self.subTest(lote_id=lote_id):
                resposta = self.client.get(reverse('movimentacao-estoque-list'), {'lote_id': lote_id})
                self.assertEqual(resposta.status_code, 400, resposta.data)

    def test_rastreabilidade_deriva_origem_fornecedor_e_historico_do_lote(self):
        self.receber([self.lote_recebimento('500', numero='ORIGEM-FORNECEDOR')])
        lote = LoteEstoque.objects.get(
            estoque__item_generico=self.genero,
            numero_lote='ORIGEM-FORNECEDOR',
        )
        registrar_saida(
            item_generico_id=self.genero.id,
            quantidade='20',
            tipo_saida='PRODUCAO',
            justificativa='Consumo de teste',
            usuario=self.estoquista,
        )

        resposta = self.resposta_rastreabilidade(lote)
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.data['origem']['tipo'], 'FORNECEDOR')
        self.assertEqual(resposta.data['origem']['ordem_codigo'], self.ordem.codigo)
        self.assertEqual(resposta.data['origem']['fornecedor_nome'], 'T. LEITE SILVA')
        self.assertEqual(resposta.data['origem']['empenho_codigo'], self.empenho.codigo)
        self.assertEqual(resposta.data['origem']['ata_numero'], self.empenho.ata.numero_ata)
        self.assertEqual(Decimal(resposta.data['origem']['quantidade_origem']), Decimal('500.000'))
        self.assertEqual([item['sentido'] for item in resposta.data['movimentacoes']], ['S', 'E'])
        self.assertEqual(Decimal(resposta.data['movimentacoes'][0]['quantidade_lote']), Decimal('20.000'))
        self.assertEqual(Decimal(resposta.data['movimentacoes'][0]['saldo_lote_resultante']), Decimal('480.000'))
        self.assertEqual(Decimal(resposta.data['movimentacoes'][1]['saldo_lote_resultante']), Decimal('500.000'))

    def test_rastreabilidade_identifica_carga_inicial_inventario_e_legado(self):
        self.registrar_carga_teste('10', numero='ORIGEM-CARGA')
        lote_carga = LoteEstoque.objects.get(
            estoque__item_generico=self.genero,
            numero_lote='ORIGEM-CARGA',
        )
        resposta = self.resposta_rastreabilidade(lote_carga)
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.data['origem']['tipo'], 'CARGA_INICIAL')
        self.assertIsNone(resposta.data['origem']['fornecedor_nome'])
        self.assertIsNone(resposta.data['origem']['ordem_codigo'])

        outro_genero = ItemGenerico.objects.create(
            catmat='654321', descricao='Feijão para inventário', unidade_medida='KG', categoria='NP',
        )
        registrar_ajuste(
            item_generico_id=outro_genero.id,
            lotes=[{
                'numero_lote': 'ORIGEM-INVENTARIO',
                'data_validade': '2099-12-31',
                'quantidade_contada': '8',
            }],
            justificativa='Lote encontrado no inventário',
            usuario=self.estoquista,
        )
        lote_inventario = LoteEstoque.objects.get(
            estoque__item_generico=outro_genero,
            numero_lote='ORIGEM-INVENTARIO',
        )
        resposta = self.resposta_rastreabilidade(lote_inventario)
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.data['origem']['tipo'], 'INVENTARIO')
        self.assertIsNotNone(resposta.data['origem']['inventario_id'])

        lote_legado = self.lote_estoque('LEGADO', '5', legado=True)
        resposta = self.resposta_rastreabilidade(lote_legado)
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.data['origem']['tipo'], 'LEGADO')

    def test_rastreabilidade_rejeita_lote_inexistente_e_respeita_permissao(self):
        resposta = self.client.get(
            reverse('movimentacao-estoque-rastreabilidade-lote'),
            {'lote_id': 999999},
        )
        self.assertEqual(resposta.status_code, 404, resposta.data)

        lote = self.lote_estoque('PERMISSAO', '1', date(2099, 12, 31))
        for usuario, status_esperado in (
            (self.diretor, 200),
            (self.nutricionista, 200),
            (self.estoquista, 200),
            (self.tecnico, 403),
        ):
            with self.subTest(usuario=usuario.papel):
                self.client.force_authenticate(usuario)
                resposta = self.resposta_rastreabilidade(lote)
                self.assertEqual(resposta.status_code, status_esperado, resposta.data)


class PainelNutricionistaTests(EstoqueBaseMixin, APITestCase):
    """Home do Nutricionista: disponibilidade por gênero, movimentação semanal e saldos."""

    def setUp(self):
        self.criar_cenario()
        registrar_recebimento(
            ordem_id=self.ordem.id,
            itens_recebidos=[{
                'item_ordem_id': self.item_ordem.id, 'lotes': [self.lote_recebimento('200')],
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


class AlertasValidadeTests(EstoqueBaseMixin, APITestCase):
    def setUp(self):
        self.criar_cenario()
        self.url = reverse('lote-estoque-alertas-validade')

    def _criar_lotes_alertaveis(self):
        hoje = data_atual_estoque()
        return {
            'vencido': self.lote_estoque('ALERTA-VENCIDO', '1', hoje - timedelta(days=1)),
            'hoje': self.lote_estoque('ALERTA-HOJE', '1', hoje),
            'critico': self.lote_estoque('ALERTA-CRITICO', '1', hoje + timedelta(days=1)),
            'atencao': self.lote_estoque('ALERTA-ATENCAO', '1', hoje + timedelta(days=8)),
            'regular': self.lote_estoque('ALERTA-REGULAR', '1', hoje + timedelta(days=31)),
            'legado': self.lote_estoque('LEGADO', '1', legado=True),
            'zerado': self.lote_estoque('ALERTA-ZERADO', '0', hoje + timedelta(days=2)),
        }

    def test_alertas_validade_estoquista_incluem_vencidos_e_ate_30_dias(self):
        lotes = self._criar_lotes_alertaveis()
        self.client.force_authenticate(self.estoquista)

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.data['total'], 4)
        self.assertEqual(resposta.data['vencidos'], 1)
        self.assertEqual(resposta.data['vence_hoje'], 1)
        self.assertEqual(resposta.data['criticos'], 1)
        self.assertEqual(resposta.data['atencao'], 1)
        ids = {lote['id'] for lote in resposta.data['results']}
        self.assertEqual(ids, {
            lotes['vencido'].id,
            lotes['hoje'].id,
            lotes['critico'].id,
            lotes['atencao'].id,
        })
        self.assertNotIn(lotes['regular'].id, ids)
        self.assertNotIn(lotes['legado'].id, ids)
        self.assertNotIn(lotes['zerado'].id, ids)

    def test_alertas_validade_nutricionista_excluem_vencidos(self):
        lotes = self._criar_lotes_alertaveis()
        self.client.force_authenticate(self.nutricionista)

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.data['total'], 3)
        self.assertEqual(resposta.data['vencidos'], 0)
        self.assertEqual(resposta.data['vence_hoje'], 1)
        self.assertEqual(resposta.data['criticos'], 1)
        self.assertEqual(resposta.data['atencao'], 1)
        self.assertEqual(
            {lote['id'] for lote in resposta.data['results']},
            {lotes['hoje'].id, lotes['critico'].id, lotes['atencao'].id},
        )

    def test_alertas_validade_diretor_e_tecnico_recebem_resposta_vazia(self):
        self._criar_lotes_alertaveis()
        for usuario in (self.diretor, self.tecnico):
            with self.subTest(usuario=usuario.papel):
                self.client.force_authenticate(usuario)
                resposta = self.client.get(self.url)
                self.assertEqual(resposta.status_code, 200, resposta.data)
                self.assertEqual(resposta.data['total'], 0)
                self.assertEqual(resposta.data['results'], [])

    def test_alertas_validade_limitam_results_e_desaparecem_quando_lote_zera(self):
        hoje = data_atual_estoque()
        for indice in range(6):
            self.lote_estoque(f'ALERTA-LIMITE-{indice}', '1', hoje + timedelta(days=indice + 1))
        self.client.force_authenticate(self.estoquista)

        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200, resposta.data)
        self.assertEqual(resposta.data['total'], 6)
        self.assertEqual(len(resposta.data['results']), 5)

        lote = self.lote_estoque('ALERTA-DINAMICO', '10', hoje + timedelta(days=2))
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.data['total'], 7)
        registrar_saida(
            item_generico_id=self.genero.id,
            quantidade='10',
            tipo_saida='PERDA',
            lote_id=lote.id,
            justificativa='Baixa para teste de alerta dinâmico',
            usuario=self.estoquista,
        )
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.data['total'], 6)
        self.assertNotIn(lote.id, {item['id'] for item in resposta.data['results']})


class PainelNutricionistaValidadeTests(EstoqueBaseMixin, TestCase):
    def setUp(self):
        self.criar_cenario()
        self.referencia = date(2026, 10, 30)

    def _genero_no_painel(self, dados):
        return next(
            genero
            for genero in dados['generos']
            if genero['item_generico_id'] == self.genero.id
        )

    def test_painel_nutricionista_usa_saldo_utilizavel(self):
        self.lote_estoque('PAINEL-VENCIDO', '30', self.referencia - timedelta(days=1))
        self.lote_estoque('PAINEL-VALIDO', '70', self.referencia)

        dados = montar_painel(hoje=self.referencia)

        self.assertEqual(self._genero_no_painel(dados)['em_estoque'], Decimal('70.000'))

    def test_painel_nutricionista_inclui_lote_que_vence_hoje(self):
        self.lote_estoque('PAINEL-HOJE', '25', self.referencia)

        dados = montar_painel(hoje=self.referencia)

        self.assertEqual(self._genero_no_painel(dados)['em_estoque'], Decimal('25.000'))

    def test_painel_nutricionista_resume_lotes_utilizaveis_proximos(self):
        self.lote_estoque('PAINEL-VENCIDO', '1', self.referencia - timedelta(days=1))
        self.lote_estoque('PAINEL-HOJE', '1', self.referencia)
        self.lote_estoque('PAINEL-CRITICO', '1', self.referencia + timedelta(days=1))
        self.lote_estoque('PAINEL-ATENCAO', '1', self.referencia + timedelta(days=8))
        self.lote_estoque('PAINEL-REGULAR', '1', self.referencia + timedelta(days=31))
        self.lote_estoque('LEGADO', '1', legado=True)

        dados = montar_painel(hoje=self.referencia)

        self.assertEqual(dados['validades'], {
            'total_proximos': 3,
            'vence_hoje': 1,
            'criticos': 1,
            'atencao': 1,
        })

    def test_movimentacao_semanal_usa_dia_local_de_rio_branco(self):
        momento_utc = datetime(2026, 11, 2, 2, tzinfo=dt_timezone.utc)
        self.registrar_carga_teste(
            '10',
            numero='PAINEL-FUSO',
            validade='2099-12-31',
            data_hora=momento_utc,
        )

        dados = montar_painel(hoje=date(2026, 11, 2))
        serie = dados['movimentacao']['por_genero'][self.genero.id]

        self.assertEqual(dados['movimentacao']['semanas'][-1], '2026-11-02')
        self.assertEqual(serie['entradas'][-2], Decimal('10.000'))
        self.assertEqual(serie['entradas'][-1], Decimal('0'))


@skipUnless(connection.vendor == 'mysql', 'Teste de concorrência específico do MySQL.')
class EstoqueConcorrenciaTests(EstoqueBaseMixin, TransactionTestCase):
    def setUp(self):
        self.criar_cenario()

    def test_duas_saidas_concorrentes_respeitam_o_lock_do_estoque(self):
        self.registrar_carga_teste('100', numero='CONCORRENCIA-A')
        estoque = Estoque.objects.get(item_generico=self.genero)
        usuario_id = self.estoquista.id
        barreira = threading.Barrier(2)
        resultados = []
        erros_inesperados = []
        resultados_lock = threading.Lock()

        def registrar_saida_concorrente():
            close_old_connections()
            try:
                usuario = Usuario.objects.get(pk=usuario_id)
                barreira.wait()
                registrar_saida(
                    item_generico_id=self.genero.id,
                    quantidade='60',
                    tipo_saida='PRODUCAO',
                    justificativa='Teste de concorrência.',
                    usuario=usuario,
                )
                resultado = 'sucesso'
            except ValidationError:
                resultado = 'validacao'
            except Exception as exc:
                with resultados_lock:
                    erros_inesperados.append(exc)
                return
            finally:
                close_old_connections()

            with resultados_lock:
                resultados.append(resultado)

        primeira = threading.Thread(target=registrar_saida_concorrente)
        segunda = threading.Thread(target=registrar_saida_concorrente)
        primeira.start()
        segunda.start()
        primeira.join()
        segunda.join()

        self.assertFalse(erros_inesperados, erros_inesperados)
        self.assertEqual(resultados.count('sucesso'), 1)
        self.assertEqual(resultados.count('validacao'), 1)

        estoque.refresh_from_db()
        lote = LoteEstoque.objects.get(estoque=estoque, numero_lote='CONCORRENCIA-A')
        self.assertEqual(estoque.saldo_atual, Decimal('40.000'))
        self.assertEqual(lote.saldo_atual, Decimal('40.000'))
        self.assertEqual(MovimentacaoEstoque.objects.filter(
            estoque=estoque,
            tipo=MovimentacaoEstoque.Tipo.SAIDA_PRODUCAO,
        ).count(), 1)
        self.assert_integridade_estoque(estoque)
