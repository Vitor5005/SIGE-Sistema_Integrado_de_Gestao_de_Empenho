from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Case, Count, Exists, IntegerField, OuterRef, Prefetch, Q, Value, When
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from empenho.models import ItemEmpenho, OperacaoItem
from estoque.models import Estoque, LoteEstoque, MovimentacaoEstoque, MovimentacaoLote
from estoque.serializers import (
    AjusteSerializer,
    CargaInicialSerializer,
    EstoqueSerializer,
    EstornoSerializer,
    HistoricoMovimentacaoLoteSerializer,
    LoteInventarioSerializer,
    LoteSaidaSerializer,
    LoteValidadeSerializer,
    MovimentacaoEstoqueExtratoSerializer,
    MovimentacaoEstoqueSerializer,
    RecebimentoSerializer,
    SaidaSerializer,
)
from utils.estoque_services import (
    estornar_movimentacao,
    registrar_ajuste,
    registrar_carga_inicial,
    registrar_recebimento,
    registrar_saida,
    data_atual_estoque,
    lote_vencido,
    lotes_utilizaveis_queryset,
)
from utils.mixins import BaseFiltroMixin, FiltroQueryParamMixin, RBACMixin
from utils.painel_nutricionista import montar_painel
from utils.rbac import Acao, Papel, Recurso


class EstoqueViewSet(RBACMixin, BaseFiltroMixin, viewsets.ReadOnlyModelViewSet):
    queryset = Estoque.objects.select_related('item_generico').annotate(
        possui_carga_inicial=Exists(MovimentacaoEstoque.objects.filter(
            estoque=OuterRef('pk'), tipo=MovimentacaoEstoque.Tipo.CARGA_INICIAL,
        )),
    )
    serializer_class = EstoqueSerializer
    rbac_resource = Recurso.ESTOQUE
    rbac_action_map = {
        'consolidado': Acao.CONSULTAR_CONSOLIDADO,
        'recebimentos': Acao.REGISTRAR_RECEBIMENTO,
        'saidas': Acao.REGISTRAR_SAIDA,
        'lotes_para_perda': Acao.REGISTRAR_SAIDA,
        'lotes_para_inventario': Acao.REGISTRAR_AJUSTE,
        'cargas_iniciais': Acao.REGISTRAR_CARGA_INICIAL,
        'ajustes': Acao.REGISTRAR_AJUSTE,
        'estornos': Acao.ESTORNAR,
    }
    search_fields = [
        'item_generico__catmat', 'item_generico__descricao',
        'item_generico__unidade_medida', 'item_generico__categoria',
    ]
    filterset_fields = {'item_generico__categoria': ['exact']}
    ordering_fields = ['item_generico__descricao', 'item_generico__categoria', 'saldo_atual']
    ordering = ['item_generico__descricao']

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            Prefetch(
                'lotes',
                queryset=lotes_utilizaveis_queryset(),
                to_attr='lotes_utilizaveis_prefetch',
            ),
        )

    @action(detail=False, methods=['get'])
    def consolidado(self, request):
        itens = ItemEmpenho.objects.select_related(
            'empenho', 'item_ata__item_generico'
        ).all().order_by('empenho__codigo', 'item_ata__item_generico__descricao')

        operacoes = defaultdict(lambda: Decimal('0.00'))
        for operacao in OperacaoItem.objects.values('item_empenho__item_ata_id', 'tipo', 'valor'):
            sinal = Decimal('-1') if operacao['tipo'] == 'anl' else Decimal('1')
            operacoes[operacao['item_empenho__item_ata_id']] += sinal * operacao['valor']

        saldos = dict(Estoque.objects.values_list('item_generico_id', 'saldo_atual'))
        dados = []
        for item in itens:
            item_ata = item.item_ata
            genero = item_ata.item_generico
            dados.append({
                'empenho_id': item.empenho_id,
                'empenho': item.empenho.codigo,
                'item_generico_id': genero.id,
                'catmat': genero.catmat,
                'descricao': genero.descricao,
                'unidade_medida': genero.unidade_medida,
                'categoria': genero.categoria,
                'imagem': request.build_absolute_uri(genero.imagem.url) if genero.imagem else None,
                'saldo_ata': item_ata.quantidade_licitada - operacoes[item_ata.id],
                'saldo_empenho': item.quantidade_atual,
                'saldo_estoque': saldos.get(genero.id, Decimal('0.000')),
            })
        return Response(dados)

    def _executar(self, serializer_class, servico, request):
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        resultado = servico(usuario=request.user, **serializer.validated_data)
        movimento = resultado[1] if isinstance(resultado, tuple) else resultado
        if isinstance(movimento, list):
            dados = MovimentacaoEstoqueSerializer(movimento, many=True).data
        else:
            dados = MovimentacaoEstoqueSerializer(movimento).data
        return Response(dados, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def recebimentos(self, request):
        serializer = RecebimentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ordem, movimentos = registrar_recebimento(
            ordem_id=serializer.validated_data['ordem_id'],
            itens_recebidos=serializer.validated_data['itens'],
            data_entrada=serializer.validated_data.get('data_entrada'),
            usuario=request.user,
        )
        return Response({
            'ordem_id': ordem.id,
            'status': ordem.status,
            'valor_total_recebido': ordem.valor_total_executado,
            'movimentacoes': MovimentacaoEstoqueSerializer(movimentos, many=True).data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def saidas(self, request):
        return self._executar(SaidaSerializer, registrar_saida, request)

    @action(detail=False, methods=['get'], url_path='lotes-para-perda')
    def lotes_para_perda(self, request):
        try:
            item_generico_id = int(request.query_params.get('item_generico_id'))
        except (TypeError, ValueError) as exc:
            raise ValidationError({
                'item_generico_id': 'Informe um g\u00eanero v\u00e1lido.',
            }) from exc
        if item_generico_id <= 0:
            raise ValidationError({'item_generico_id': 'Informe um g\u00eanero v\u00e1lido.'})

        lotes = list(
            LoteEstoque.objects.filter(
                estoque__item_generico_id=item_generico_id,
                saldo_atual__gt=0,
            )
        )
        lotes.sort(key=lambda lote: (
            0 if not lote.legado and lote_vencido(lote) else (1 if not lote.legado else 2),
            lote.data_validade if lote.data_validade is not None else date.max,
            lote.id,
        ))
        return Response(LoteSaidaSerializer(lotes, many=True).data)

    @action(detail=False, methods=['get'], url_path='lotes-para-inventario')
    def lotes_para_inventario(self, request):
        try:
            item_generico_id = int(request.query_params.get('item_generico_id'))
        except (TypeError, ValueError) as exc:
            raise ValidationError({
                'item_generico_id': 'Informe um gênero válido.',
            }) from exc
        if item_generico_id <= 0:
            raise ValidationError({'item_generico_id': 'Informe um gênero válido.'})

        lotes = list(
            LoteEstoque.objects.filter(
                estoque__item_generico_id=item_generico_id,
                saldo_atual__gt=0,
            )
        )
        lotes.sort(key=lambda lote: (
            0 if lote.legado else 1,
            lote.data_validade if lote.data_validade is not None else date.max,
            lote.id,
        ))
        return Response(LoteInventarioSerializer(lotes, many=True).data)

    @action(detail=False, methods=['post'], url_path='cargas-iniciais')
    def cargas_iniciais(self, request):
        return self._executar(CargaInicialSerializer, registrar_carga_inicial, request)

    @action(detail=False, methods=['post'])
    def ajustes(self, request):
        return self._executar(AjusteSerializer, registrar_ajuste, request)

    @action(detail=False, methods=['post'])
    def estornos(self, request):
        return self._executar(EstornoSerializer, estornar_movimentacao, request)


class LoteEstoqueViewSet(RBACMixin, BaseFiltroMixin, viewsets.ReadOnlyModelViewSet):
    queryset = LoteEstoque.objects.select_related('estoque__item_generico')
    serializer_class = LoteValidadeSerializer
    rbac_resource = Recurso.ESTOQUE
    rbac_action_map = {
        'resumo': Acao.CONSULTAR,
        'alertas_validade': Acao.CONSULTAR,
    }
    search_fields = [
        'numero_lote',
        'estoque__item_generico__catmat',
        'estoque__item_generico__descricao',
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        saldo_positivo = params.get('saldo_positivo', 'true').strip().lower()
        if saldo_positivo in {'true', '1'}:
            queryset = queryset.filter(saldo_atual__gt=0)
        elif saldo_positivo not in {'false', '0'}:
            raise ValidationError({
                'saldo_positivo': 'Informe saldo_positivo como true ou false.',
            })

        categoria = params.get('categoria')
        if categoria:
            queryset = queryset.filter(estoque__item_generico__categoria=categoria)

        item_generico_id = params.get('item_generico_id')
        if item_generico_id is not None:
            try:
                item_generico_id = int(item_generico_id)
            except (TypeError, ValueError) as exc:
                raise ValidationError({
                    'item_generico_id': 'Informe um gênero válido.',
                }) from exc
            if item_generico_id <= 0:
                raise ValidationError({'item_generico_id': 'Informe um gênero válido.'})
            queryset = queryset.filter(estoque__item_generico_id=item_generico_id)

        hoje = data_atual_estoque()
        status_validade = params.get('status')
        if status_validade is not None:
            filtros_status = {
                'VENCIDO': Q(legado=False, data_validade__lt=hoje),
                'VENCE_HOJE': Q(legado=False, data_validade=hoje),
                'CRITICO': Q(
                    legado=False,
                    data_validade__gte=hoje + timedelta(days=1),
                    data_validade__lte=hoje + timedelta(days=7),
                ),
                'ATENCAO': Q(
                    legado=False,
                    data_validade__gte=hoje + timedelta(days=8),
                    data_validade__lte=hoje + timedelta(days=30),
                ),
                'REGULAR': Q(legado=False, data_validade__gt=hoje + timedelta(days=30)),
                'SEM_VALIDADE': Q(legado=True) | Q(data_validade__isnull=True),
            }
            if status_validade not in filtros_status:
                raise ValidationError({
                    'status': 'Informe um status de validade válido.',
                })
            queryset = queryset.filter(filtros_status[status_validade])

        for campo in ('data_validade__gte', 'data_validade__lte'):
            valor = params.get(campo)
            if valor is not None:
                data_validade = parse_date(valor)
                if data_validade is None:
                    raise ValidationError({
                        'data_validade': 'Informe uma data de validade válida.',
                    })
                queryset = queryset.filter(**{campo: data_validade})

        return queryset.annotate(
            ordem_sem_validade=Case(
                When(data_validade__isnull=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        ).order_by(
            'ordem_sem_validade',
            'data_validade',
            'estoque__item_generico__descricao',
            'numero_lote',
            'id',
        )

    @action(detail=False, methods=['get'])
    def resumo(self, request):
        hoje = data_atual_estoque()
        totais = LoteEstoque.objects.filter(saldo_atual__gt=0).aggregate(
            total_lotes=Count('id'),
            vencidos=Count('id', filter=Q(legado=False, data_validade__lt=hoje)),
            vence_hoje=Count('id', filter=Q(legado=False, data_validade=hoje)),
            criticos=Count(
                'id',
                filter=Q(
                    legado=False,
                    data_validade__gte=hoje + timedelta(days=1),
                    data_validade__lte=hoje + timedelta(days=7),
                ),
            ),
            atencao=Count(
                'id',
                filter=Q(
                    legado=False,
                    data_validade__gte=hoje + timedelta(days=8),
                    data_validade__lte=hoje + timedelta(days=30),
                ),
            ),
            regulares=Count('id', filter=Q(legado=False, data_validade__gt=hoje + timedelta(days=30))),
            sem_validade=Count(
                'id',
                filter=Q(legado=True) | Q(data_validade__isnull=True),
            ),
        )
        return Response(totais)

    @action(detail=False, methods=['get'], url_path='alertas-validade')
    def alertas_validade(self, request):
        resposta_vazia = {
            'total': 0,
            'vencidos': 0,
            'vence_hoje': 0,
            'criticos': 0,
            'atencao': 0,
            'results': [],
        }
        if request.user.papel not in {Papel.ESTOQUISTA, Papel.NUTRICIONISTA}:
            return Response(resposta_vazia)

        hoje = data_atual_estoque()
        limite = hoje + timedelta(days=30)
        lotes = LoteEstoque.objects.filter(
            saldo_atual__gt=0,
            legado=False,
            data_validade__isnull=False,
            data_validade__lte=limite,
        ).select_related('estoque__item_generico')
        if request.user.papel == Papel.NUTRICIONISTA:
            lotes = lotes.filter(data_validade__gte=hoje)

        totais = lotes.aggregate(
            total=Count('id'),
            vencidos=Count('id', filter=Q(data_validade__lt=hoje)),
            vence_hoje=Count('id', filter=Q(data_validade=hoje)),
            criticos=Count(
                'id',
                filter=Q(
                    data_validade__gte=hoje + timedelta(days=1),
                    data_validade__lte=hoje + timedelta(days=7),
                ),
            ),
            atencao=Count(
                'id',
                filter=Q(
                    data_validade__gte=hoje + timedelta(days=8),
                    data_validade__lte=limite,
                ),
            ),
        )
        resultados = lotes.order_by(
            'data_validade',
            'estoque__item_generico__descricao',
            'numero_lote',
            'id',
        )[:5]
        return Response({
            **totais,
            'results': LoteValidadeSerializer(resultados, many=True).data,
        })


class MovimentacaoEstoqueViewSet(RBACMixin, BaseFiltroMixin, FiltroQueryParamMixin, viewsets.ReadOnlyModelViewSet):
    queryset = MovimentacaoEstoque.objects.select_related(
        'estoque__item_generico',
        'usuario',
        'item_ordem__ordem_entrega',
        'item_inventario__inventario',
        'item_cardapio__cardapio',
    ).prefetch_related('alocacoes_lote__lote').all()
    serializer_class = MovimentacaoEstoqueExtratoSerializer
    rbac_resource = Recurso.MOVIMENTACAO_ESTOQUE
    rbac_action_map = {
        'list': Acao.CONSULTAR_EXTRATO,
        'retrieve': Acao.CONSULTAR_EXTRATO,
        'rastreabilidade_lote': Acao.CONSULTAR_EXTRATO,
    }
    search_fields = ['estoque__item_generico__catmat', 'estoque__item_generico__descricao', 'observacao']
    ordering_fields = ['data_hora', 'quantidade', 'saldo_resultante']
    ordering = ['-data_hora', '-id']
    filtros_query_param = {
        'genero_id': 'estoque__item_generico_id',
        'data_inicio': 'data_hora__gte',
        'data_fim': 'data_hora__lte',
    }

    @staticmethod
    def _lote_id_valido(request):
        try:
            lote_id = int(request.query_params.get('lote_id'))
        except (TypeError, ValueError) as exc:
            raise ValidationError({'lote_id': 'Informe um lote válido.'}) from exc
        if lote_id <= 0:
            raise ValidationError({'lote_id': 'Informe um lote válido.'})
        return lote_id

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('lote_id') is None:
            return queryset
        lote_id = self._lote_id_valido(self.request)
        return queryset.filter(alocacoes_lote__lote_id=lote_id)

    @staticmethod
    def _origem_lote(lote):
        origem_vazia = {
            'movimentacao_id': None,
            'data_hora': None,
            'quantidade_origem': None,
            'ordem_codigo': None,
            'fornecedor_nome': None,
            'empenho_codigo': None,
            'ata_numero': None,
            'inventario_id': None,
        }
        if lote.legado:
            return {
                **origem_vazia,
                'tipo': 'LEGADO',
                'descricao': 'Saldo histórico anterior ao controle por lotes',
            }

        origem = (
            MovimentacaoLote.objects.filter(
                lote=lote,
                movimentacao__sentido=MovimentacaoEstoque.Sentido.ENTRADA,
                movimentacao__tipo__in=(
                    MovimentacaoEstoque.Tipo.ENTRADA_FORNECEDOR,
                    MovimentacaoEstoque.Tipo.CARGA_INICIAL,
                    MovimentacaoEstoque.Tipo.AJUSTE_POSITIVO,
                ),
            )
            .select_related(
                'movimentacao__item_ordem__ordem_entrega',
                'movimentacao__item_ordem__item_empenho__empenho__ata__fornecedor',
                'movimentacao__item_inventario__inventario',
            )
            .order_by('movimentacao__data_hora', 'movimentacao_id', 'id')
            .first()
        )
        if origem is None:
            return {
                **origem_vazia,
                'tipo': 'NAO_IDENTIFICADA',
                'descricao': 'Origem não identificada',
            }

        movimentacao = origem.movimentacao
        dados = {
            **origem_vazia,
            'movimentacao_id': movimentacao.id,
            'data_hora': movimentacao.data_hora,
            'quantidade_origem': origem.quantidade,
        }
        if movimentacao.tipo == MovimentacaoEstoque.Tipo.ENTRADA_FORNECEDOR:
            item_ordem = movimentacao.item_ordem
            ordem = item_ordem.ordem_entrega if item_ordem is not None else None
            item_empenho = item_ordem.item_empenho if item_ordem is not None else None
            empenho = item_empenho.empenho if item_empenho is not None else None
            ata = empenho.ata if empenho is not None else None
            fornecedor = ata.fornecedor if ata is not None else None
            return {
                **dados,
                'tipo': 'FORNECEDOR',
                'descricao': 'Recebimento de fornecedor',
                'ordem_codigo': ordem.codigo if ordem is not None else None,
                'fornecedor_nome': (
                    fornecedor.nome_fantasia or fornecedor.razao_social
                    if fornecedor is not None
                    else None
                ),
                'empenho_codigo': empenho.codigo if empenho is not None else None,
                'ata_numero': ata.numero_ata if ata is not None else None,
            }
        if movimentacao.tipo == MovimentacaoEstoque.Tipo.CARGA_INICIAL:
            return {
                **dados,
                'tipo': 'CARGA_INICIAL',
                'descricao': 'Carga inicial de estoque',
            }
        if movimentacao.tipo == MovimentacaoEstoque.Tipo.AJUSTE_POSITIVO:
            item_inventario = movimentacao.item_inventario
            return {
                **dados,
                'tipo': 'INVENTARIO',
                'descricao': 'Lote identificado em inventário',
                'inventario_id': item_inventario.inventario_id if item_inventario is not None else None,
            }
        return {
            **origem_vazia,
            'tipo': 'NAO_IDENTIFICADA',
            'descricao': 'Origem não identificada',
        }

    @action(detail=False, methods=['get'], url_path='rastreabilidade-lote')
    def rastreabilidade_lote(self, request):
        lote_id = self._lote_id_valido(request)
        lote = get_object_or_404(
            LoteEstoque.objects.select_related('estoque__item_generico'),
            pk=lote_id,
        )
        movimentacoes = (
            MovimentacaoLote.objects.filter(lote=lote)
            .select_related(
                'movimentacao',
                'movimentacao__usuario',
                'movimentacao__item_ordem__ordem_entrega',
                'movimentacao__item_ordem__item_empenho__empenho__ata__fornecedor',
                'movimentacao__item_inventario__inventario',
                'movimentacao__item_cardapio__cardapio',
                'movimentacao__movimentacao_estornada',
            )
            .order_by('-movimentacao__data_hora', '-movimentacao_id', '-id')
        )
        return Response({
            'lote': LoteValidadeSerializer(lote).data,
            'origem': self._origem_lote(lote),
            'movimentacoes': HistoricoMovimentacaoLoteSerializer(movimentacoes, many=True).data,
        })


class PainelNutricionistaViewSet(RBACMixin, viewsets.ViewSet):
    """Resumo de estoque, movimentação, empenhos e ARPs para a Home do Nutricionista."""
    rbac_resource = Recurso.PAINEL_NUTRICIONISTA

    def list(self, request):
        return Response(montar_painel())
