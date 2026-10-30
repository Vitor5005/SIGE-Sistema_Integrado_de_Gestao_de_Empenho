from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import DatabaseError, transaction
from django.db.models import Sum
from django.test import TestCase
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
from utils.estoque_services import (
    estornar_movimentacao,
    registrar_ajuste,
    registrar_carga_inicial,
    registrar_recebimento,
    registrar_saida,
    FUSO_ESTOQUE,
    saldo_utilizavel_estoque,
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
