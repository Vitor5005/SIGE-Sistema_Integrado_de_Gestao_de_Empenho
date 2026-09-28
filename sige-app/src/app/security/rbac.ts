export enum Papel {
  DIRETOR = 'DIRET',
  TECNICO_ADMINISTRATIVO = 'TECAD',
  NUTRICIONISTA = 'NUTRI',
  ESTOQUISTA = 'ESTOQ',
}

export enum Recurso {
  USUARIO = 'usuario',
  ENDERECO = 'endereco',
  FORNECEDOR = 'fornecedor',
  GENERO_ALIMENTICIO = 'genero_alimenticio',
  LICITACAO = 'licitacao',
  ATA = 'ata',
  ITEM_ATA = 'item_ata',
  EMPENHO = 'empenho',
  ITEM_EMPENHO = 'item_empenho',
  OPERACAO_EMPENHO = 'operacao_empenho',
  ORDEM_ENTREGA = 'ordem_entrega',
  ITEM_ORDEM = 'item_ordem',
  HISTORICO = 'historico',
  ESTOQUE = 'estoque',
  MOVIMENTACAO_ESTOQUE = 'movimentacao_estoque',
  INVENTARIO = 'inventario',
  PENDENCIA_FORNECEDOR = 'pendencia_fornecedor',
  SOLICITACAO_REFORCO = 'solicitacao_reforco',
  PAINEL_NUTRICIONISTA = 'painel_nutricionista',
}

export enum Acao {
  CONSULTAR = 'consultar',
  CADASTRAR = 'cadastrar',
  EDITAR = 'editar',
  EXCLUIR = 'excluir',
  DEFINIR_ATUAL = 'definir_atual',
  ATRIBUIR_PAPEL = 'atribuir_papel',
  ALTERAR_STATUS = 'alterar_status',
  SOLICITAR_REFORCO = 'solicitar_reforco',
  INCLUIR_EMPENHO = 'incluir_empenho',
  REFORCAR_EMPENHO = 'reforcar_empenho',
  ANULAR_EMPENHO = 'anular_empenho',
  GERAR_ORDEM = 'gerar_ordem',
  EMITIR_ORDEM = 'emitir_ordem',
  REGISTRAR_RECEBIMENTO = 'registrar_recebimento',
  REGISTRAR_SAIDA = 'registrar_saida',
  REGISTRAR_CARGA_INICIAL = 'registrar_carga_inicial',
  REGISTRAR_AJUSTE = 'registrar_ajuste',
  ESTORNAR = 'estornar',
  CONSULTAR_EXTRATO = 'consultar_extrato',
  CONSULTAR_CONSOLIDADO = 'consultar_consolidado',
}

type Matriz = Partial<Record<Recurso, Partial<Record<Acao, readonly Papel[]>>>>;

const DIRETOR = [Papel.DIRETOR] as const;
const TODOS = [Papel.DIRETOR, Papel.TECNICO_ADMINISTRATIVO, Papel.NUTRICIONISTA] as const;
const DIRETOR_TECNICO = [Papel.DIRETOR, Papel.TECNICO_ADMINISTRATIVO] as const;
const TODOS_COM_ESTOQUISTA = [...TODOS, Papel.ESTOQUISTA] as const;
const DIRETOR_NUTRICIONISTA_ESTOQUISTA = [Papel.DIRETOR, Papel.NUTRICIONISTA, Papel.ESTOQUISTA] as const;
const DIRETOR_TECNICO_ESTOQUISTA = [Papel.DIRETOR, Papel.TECNICO_ADMINISTRATIVO, Papel.ESTOQUISTA] as const;
const ESTOQUISTA = [Papel.ESTOQUISTA] as const;

export const MATRIZ_PERMISSOES: Matriz = {
  [Recurso.USUARIO]: {
    [Acao.CONSULTAR]: DIRETOR,
    [Acao.CADASTRAR]: DIRETOR,
    [Acao.EDITAR]: DIRETOR,
    [Acao.ATRIBUIR_PAPEL]: DIRETOR,
    [Acao.ALTERAR_STATUS]: DIRETOR,
  },
  [Recurso.ENDERECO]: {
    [Acao.CONSULTAR]: DIRETOR_TECNICO,
    [Acao.CADASTRAR]: DIRETOR,
    [Acao.EDITAR]: DIRETOR,
  },
  [Recurso.FORNECEDOR]: {
    [Acao.CONSULTAR]: DIRETOR_TECNICO,
    [Acao.CADASTRAR]: DIRETOR,
    [Acao.EDITAR]: DIRETOR,
    [Acao.EXCLUIR]: DIRETOR,
  },
  [Recurso.GENERO_ALIMENTICIO]: {
    [Acao.CONSULTAR]: TODOS_COM_ESTOQUISTA,
    [Acao.CADASTRAR]: DIRETOR_TECNICO_ESTOQUISTA,
    [Acao.EDITAR]: DIRETOR_TECNICO_ESTOQUISTA,
    [Acao.EXCLUIR]: DIRETOR,
  },
  [Recurso.LICITACAO]: {
    [Acao.CONSULTAR]: TODOS,
    [Acao.CADASTRAR]: DIRETOR,
    [Acao.EDITAR]: DIRETOR,
    [Acao.EXCLUIR]: DIRETOR,
    [Acao.DEFINIR_ATUAL]: DIRETOR,
  },
  [Recurso.ATA]: {
    [Acao.CONSULTAR]: TODOS,
    [Acao.CADASTRAR]: DIRETOR,
    [Acao.EDITAR]: DIRETOR,
    [Acao.EXCLUIR]: DIRETOR,
  },
  [Recurso.ITEM_ATA]: {
    [Acao.CONSULTAR]: TODOS,
    [Acao.CADASTRAR]: DIRETOR,
    [Acao.EDITAR]: DIRETOR,
  },
  [Recurso.EMPENHO]: {
    [Acao.CONSULTAR]: TODOS,
    [Acao.CADASTRAR]: DIRETOR,
    [Acao.EDITAR]: DIRETOR,
  },
  [Recurso.ITEM_EMPENHO]: {
    [Acao.CONSULTAR]: TODOS,
    [Acao.CADASTRAR]: DIRETOR,
    [Acao.EDITAR]: DIRETOR,
    [Acao.GERAR_ORDEM]: [Papel.TECNICO_ADMINISTRATIVO],
  },
  [Recurso.OPERACAO_EMPENHO]: {
    [Acao.CONSULTAR]: DIRETOR_TECNICO,
    [Acao.INCLUIR_EMPENHO]: DIRETOR,
    [Acao.REFORCAR_EMPENHO]: DIRETOR,
    [Acao.ANULAR_EMPENHO]: DIRETOR,
  },
  [Recurso.ORDEM_ENTREGA]: {
    // TODO: restringir Nutricionista às ordens das próprias solicitações
    // quando Solicitação de Alimentos existir no domínio.
    [Acao.CONSULTAR]: TODOS_COM_ESTOQUISTA,
    [Acao.CADASTRAR]: [Papel.TECNICO_ADMINISTRATIVO],
    [Acao.GERAR_ORDEM]: [Papel.TECNICO_ADMINISTRATIVO],
    [Acao.EMITIR_ORDEM]: [Papel.TECNICO_ADMINISTRATIVO],
  },
  [Recurso.ITEM_ORDEM]: {
    [Acao.CONSULTAR]: TODOS_COM_ESTOQUISTA,
    [Acao.CADASTRAR]: [Papel.TECNICO_ADMINISTRATIVO],
    [Acao.GERAR_ORDEM]: [Papel.TECNICO_ADMINISTRATIVO],
  },
  [Recurso.HISTORICO]: {
    [Acao.CONSULTAR]: DIRETOR_TECNICO,
  },
  [Recurso.ESTOQUE]: {
    [Acao.CONSULTAR]: TODOS_COM_ESTOQUISTA,
    [Acao.CONSULTAR_CONSOLIDADO]: DIRETOR_TECNICO_ESTOQUISTA,
    [Acao.REGISTRAR_RECEBIMENTO]: ESTOQUISTA,
    [Acao.REGISTRAR_SAIDA]: ESTOQUISTA,
    [Acao.REGISTRAR_CARGA_INICIAL]: ESTOQUISTA,
    [Acao.REGISTRAR_AJUSTE]: ESTOQUISTA,
    [Acao.ESTORNAR]: ESTOQUISTA,
  },
  [Recurso.MOVIMENTACAO_ESTOQUE]: {
    [Acao.CONSULTAR_EXTRATO]: DIRETOR_NUTRICIONISTA_ESTOQUISTA,
  },
  [Recurso.INVENTARIO]: {
    [Acao.CONSULTAR]: ESTOQUISTA,
    [Acao.CADASTRAR]: ESTOQUISTA,
  },
  [Recurso.PENDENCIA_FORNECEDOR]: {
    [Acao.CONSULTAR]: DIRETOR_TECNICO_ESTOQUISTA,
    [Acao.ALTERAR_STATUS]: DIRETOR_TECNICO,
  },
  [Recurso.SOLICITACAO_REFORCO]: {
    [Acao.CONSULTAR]: [Papel.DIRETOR, Papel.NUTRICIONISTA],
    [Acao.CADASTRAR]: [Papel.NUTRICIONISTA],
    [Acao.REFORCAR_EMPENHO]: DIRETOR,
    [Acao.ALTERAR_STATUS]: DIRETOR,
  },
  [Recurso.PAINEL_NUTRICIONISTA]: {
    [Acao.CONSULTAR]: [Papel.NUTRICIONISTA],
  },
};

type TokenPayload = {
  papel?: Papel;
};

export function obterPapelAtual(): Papel | null {
  const token = localStorage.getItem('access_token');
  if (!token) return null;

  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const json = decodeURIComponent(
      atob(base64).split('').map(c => `%${(`00${c.charCodeAt(0).toString(16)}`).slice(-2)}`).join('')
    );
    return (JSON.parse(json) as TokenPayload).papel ?? null;
  } catch {
    return null;
  }
}

export function temPermissao(papel: Papel | null, recurso: Recurso, acao: Acao): boolean {
  if (!papel) return false;
  return MATRIZ_PERMISSOES[recurso]?.[acao]?.includes(papel) ?? false;
}

export function pode(recurso: Recurso, acao: Acao): boolean {
  return temPermissao(obterPapelAtual(), recurso, acao);
}
