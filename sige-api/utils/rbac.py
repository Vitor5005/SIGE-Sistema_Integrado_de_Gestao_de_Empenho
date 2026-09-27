class Papel:
    DIRETOR = 'DIRET'
    TECNICO_ADMINISTRATIVO = 'TECAD'
    NUTRICIONISTA = 'NUTRI'
    ESTOQUISTA = 'ESTOQ'

    CHOICES = (
        (DIRETOR, 'Diretor'),
        (TECNICO_ADMINISTRATIVO, 'Técnico Administrativo'),
        (NUTRICIONISTA, 'Nutricionista'),
        (ESTOQUISTA, 'Estoquista'),
    )


class Recurso:
    USUARIO = 'usuario'
    ENDERECO = 'endereco'
    FORNECEDOR = 'fornecedor'
    GENERO_ALIMENTICIO = 'genero_alimenticio'
    LICITACAO = 'licitacao'
    ATA = 'ata'
    ITEM_ATA = 'item_ata'
    EMPENHO = 'empenho'
    ITEM_EMPENHO = 'item_empenho'
    OPERACAO_EMPENHO = 'operacao_empenho'
    ORDEM_ENTREGA = 'ordem_entrega'
    ITEM_ORDEM = 'item_ordem'
    HISTORICO = 'historico'
    ESTOQUE = 'estoque'
    MOVIMENTACAO_ESTOQUE = 'movimentacao_estoque'
    INVENTARIO = 'inventario'


class Acao:
    CONSULTAR = 'consultar'
    CADASTRAR = 'cadastrar'
    EDITAR = 'editar'
    EXCLUIR = 'excluir'
    DEFINIR_ATUAL = 'definir_atual'
    ATRIBUIR_PAPEL = 'atribuir_papel'
    ALTERAR_STATUS = 'alterar_status'
    INCLUIR_EMPENHO = 'incluir_empenho'
    REFORCAR_EMPENHO = 'reforcar_empenho'
    ANULAR_EMPENHO = 'anular_empenho'
    GERAR_ORDEM = 'gerar_ordem'
    EMITIR_ORDEM = 'emitir_ordem'
    REGISTRAR_RECEBIMENTO = 'registrar_recebimento'
    REGISTRAR_SAIDA = 'registrar_saida'
    REGISTRAR_CARGA_INICIAL = 'registrar_carga_inicial'
    REGISTRAR_AJUSTE = 'registrar_ajuste'
    ESTORNAR = 'estornar'
    CONSULTAR_EXTRATO = 'consultar_extrato'
    CONSULTAR_CONSOLIDADO = 'consultar_consolidado'


DIRETOR = frozenset({Papel.DIRETOR})
TODOS = frozenset({Papel.DIRETOR, Papel.TECNICO_ADMINISTRATIVO, Papel.NUTRICIONISTA})
DIRETOR_TECNICO = frozenset({Papel.DIRETOR, Papel.TECNICO_ADMINISTRATIVO})
TODOS_COM_ESTOQUISTA = TODOS | frozenset({Papel.ESTOQUISTA})
DIRETOR_NUTRICIONISTA_ESTOQUISTA = frozenset({
    Papel.DIRETOR, Papel.NUTRICIONISTA, Papel.ESTOQUISTA,
})
DIRETOR_TECNICO_ESTOQUISTA = frozenset({
    Papel.DIRETOR, Papel.TECNICO_ADMINISTRATIVO, Papel.ESTOQUISTA,
})
ESTOQUISTA = frozenset({Papel.ESTOQUISTA})


MATRIZ_PERMISSOES = {
    Recurso.USUARIO: {
        Acao.CONSULTAR: DIRETOR,
        Acao.CADASTRAR: DIRETOR,
        Acao.EDITAR: DIRETOR,
        Acao.ATRIBUIR_PAPEL: DIRETOR,
        Acao.ALTERAR_STATUS: DIRETOR,
    },
    Recurso.ENDERECO: {
        Acao.CONSULTAR: DIRETOR_TECNICO,
        Acao.CADASTRAR: DIRETOR,
        Acao.EDITAR: DIRETOR,
    },
    Recurso.FORNECEDOR: {
        Acao.CONSULTAR: DIRETOR_TECNICO,
        Acao.CADASTRAR: DIRETOR,
        Acao.EDITAR: DIRETOR,
    },
    Recurso.GENERO_ALIMENTICIO: {
        Acao.CONSULTAR: TODOS,
        Acao.CADASTRAR: DIRETOR,
        Acao.EDITAR: DIRETOR,
    },
    Recurso.LICITACAO: {
        Acao.CONSULTAR: TODOS,
        Acao.CADASTRAR: DIRETOR,
        Acao.EDITAR: DIRETOR,
        Acao.DEFINIR_ATUAL: DIRETOR,
    },
    Recurso.ATA: {
        Acao.CONSULTAR: TODOS,
        # TODO: tornar a geração automática após a licitação.
        Acao.CADASTRAR: DIRETOR,
        Acao.EDITAR: DIRETOR,
    },
    Recurso.ITEM_ATA: {
        Acao.CONSULTAR: TODOS,
        Acao.CADASTRAR: DIRETOR,
        Acao.EDITAR: DIRETOR,
    },
    Recurso.EMPENHO: {
        Acao.CONSULTAR: TODOS,
        # TODO: tornar a geração automática após a licitação.
        Acao.CADASTRAR: DIRETOR,
        Acao.EDITAR: DIRETOR,
    },
    Recurso.ITEM_EMPENHO: {
        Acao.CONSULTAR: TODOS,
        Acao.CADASTRAR: DIRETOR,
        Acao.EDITAR: DIRETOR,
        Acao.GERAR_ORDEM: frozenset({Papel.TECNICO_ADMINISTRATIVO}),
    },
    Recurso.OPERACAO_EMPENHO: {
        Acao.CONSULTAR: DIRETOR_TECNICO,
        Acao.INCLUIR_EMPENHO: DIRETOR,
        Acao.REFORCAR_EMPENHO: DIRETOR,
        Acao.ANULAR_EMPENHO: DIRETOR,
    },
    Recurso.ORDEM_ENTREGA: {
        # TODO: limitar a Nutricionista às ordens de suas solicitações quando
        # o recurso Solicitação de Alimentos existir no sistema.
        Acao.CONSULTAR: TODOS_COM_ESTOQUISTA,
        Acao.CADASTRAR: frozenset({Papel.TECNICO_ADMINISTRATIVO}),
        Acao.GERAR_ORDEM: frozenset({Papel.TECNICO_ADMINISTRATIVO}),
        Acao.EMITIR_ORDEM: frozenset({Papel.TECNICO_ADMINISTRATIVO}),
    },
    Recurso.ITEM_ORDEM: {
        Acao.CONSULTAR: TODOS_COM_ESTOQUISTA,
        Acao.CADASTRAR: frozenset({Papel.TECNICO_ADMINISTRATIVO}),
        Acao.GERAR_ORDEM: frozenset({Papel.TECNICO_ADMINISTRATIVO}),
    },
    Recurso.HISTORICO: {
        Acao.CONSULTAR: DIRETOR_TECNICO,
    },
    Recurso.ESTOQUE: {
        Acao.CONSULTAR: TODOS_COM_ESTOQUISTA,
        Acao.CONSULTAR_CONSOLIDADO: DIRETOR_TECNICO_ESTOQUISTA,
        # TODO: manter um recebimento por ordem até a definição de entregas
        # parciais em datas distintas.
        Acao.REGISTRAR_RECEBIMENTO: ESTOQUISTA,
        Acao.REGISTRAR_SAIDA: ESTOQUISTA,
        Acao.REGISTRAR_CARGA_INICIAL: ESTOQUISTA,
        Acao.REGISTRAR_AJUSTE: ESTOQUISTA,
        Acao.ESTORNAR: ESTOQUISTA,
    },
    Recurso.MOVIMENTACAO_ESTOQUE: {
        Acao.CONSULTAR_EXTRATO: DIRETOR_NUTRICIONISTA_ESTOQUISTA,
    },
    Recurso.INVENTARIO: {
        Acao.CONSULTAR: ESTOQUISTA,
        Acao.CADASTRAR: ESTOQUISTA,
    },
}


ACOES_VIEWSET = {
    'list': Acao.CONSULTAR,
    'retrieve': Acao.CONSULTAR,
    'create': Acao.CADASTRAR,
    'update': Acao.EDITAR,
    'partial_update': Acao.EDITAR,
    'destroy': Acao.EXCLUIR,
}


def resolver_acao(view, request):
    action = getattr(view, 'action', None)
    action_map = getattr(view, 'rbac_action_map', {})
    if action in action_map:
        return action_map[action]

    recurso = getattr(view, 'rbac_resource', None)
    campos = set(getattr(request, 'data', {}).keys())

    if recurso in {Recurso.ORDEM_ENTREGA, Recurso.ITEM_ORDEM} and action == 'create':
        return Acao.GERAR_ORDEM

    if recurso == Recurso.USUARIO and action in {'update', 'partial_update'}:
        if 'papel' in campos:
            return Acao.ATRIBUIR_PAPEL
        if 'is_active' in campos:
            return Acao.ALTERAR_STATUS

    if recurso == Recurso.OPERACAO_EMPENHO and action == 'create':
        return {
            'inc': Acao.INCLUIR_EMPENHO,
            'ref': Acao.REFORCAR_EMPENHO,
            'anl': Acao.ANULAR_EMPENHO,
        }.get(request.data.get('tipo'), Acao.EDITAR)

    if recurso == Recurso.ITEM_EMPENHO and action in {'update', 'partial_update'}:
        if campos == {'quantidade_entrege'}:
            return Acao.REGISTRAR_RECEBIMENTO
        if campos and campos.issubset({'quantidade_atual', 'quantidade_entrege'}):
            return Acao.GERAR_ORDEM

    if recurso == Recurso.ITEM_ORDEM and action in {'update', 'partial_update'}:
        if campos and campos.issubset({'quantidade_entregue', 'observacao'}):
            return Acao.REGISTRAR_RECEBIMENTO

    if recurso == Recurso.ORDEM_ENTREGA and action in {'update', 'partial_update'}:
        if campos and campos.issubset({'status', 'data_entrega'}):
            return Acao.REGISTRAR_RECEBIMENTO

    if recurso == Recurso.EMPENHO and action in {'update', 'partial_update'}:
        if campos == {'saldo_utilizado'}:
            return Acao.REGISTRAR_RECEBIMENTO

    return ACOES_VIEWSET.get(action)


def tem_permissao(papel, recurso, acao):
    if not papel or not recurso or not acao:
        return False
    return papel in MATRIZ_PERMISSOES.get(recurso, {}).get(acao, frozenset())

