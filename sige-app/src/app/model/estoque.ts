export interface EstoqueItem {
  id: number;
  item_generico_id: number;
  catmat: string;
  descricao: string;
  unidade_medida: string;
  categoria: string;
  categoria_descricao: string;
  conteudo_embalagem: number | null;
  unidade_embalagem: string | null;
  imagem: string | null;
  saldo_atual: number;
  saldo_utilizavel: number;
  data_atualizacao: string;
  possui_carga_inicial: boolean;
}

export interface LoteSaida {
  id: number;
  numero_lote: string;
  data_validade: string | null;
  saldo_atual: number;
  legado: boolean;
  vencido: boolean;
}

export interface LoteInventario {
  id: number;
  numero_lote: string;
  data_validade: string | null;
  saldo_atual: number;
  legado: boolean;
  vencido: boolean;
}

export type StatusValidade =
  | 'VENCIDO'
  | 'VENCE_HOJE'
  | 'CRITICO'
  | 'ATENCAO'
  | 'REGULAR'
  | 'SEM_VALIDADE';

export interface LoteValidade {
  id: number;
  estoque_id: number;
  item_generico_id: number;
  catmat: string;
  descricao: string;
  unidade_medida: string;
  categoria: string;
  categoria_descricao: string;
  numero_lote: string;
  data_validade: string | null;
  saldo_atual: number;
  legado: boolean;
  dias_para_validade: number | null;
  status: StatusValidade;
  status_descricao: string;
}

export interface ResumoValidades {
  total_lotes: number;
  vencidos: number;
  vence_hoje: number;
  criticos: number;
  atencao: number;
  regulares: number;
  sem_validade: number;
}

export interface AlertasValidade {
  total: number;
  vencidos: number;
  vence_hoje: number;
  criticos: number;
  atencao: number;
  results: LoteValidade[];
}

export interface MovimentacaoEstoque {
  id: number;
  item_generico_id: number;
  genero: string;
  tipo: string;
  tipo_descricao: string;
  sentido: 'E' | 'S';
  quantidade: number;
  saldo_resultante: number;
  data_hora: string;
  observacao: string | null;
  ordem_codigo: string | null;
  cardapio_id: number | null;
  usuario_nome: string;
  papel: string;
}

export interface AlocacaoLoteMovimentacao {
  lote_id: number;
  numero_lote: string;
  data_validade: string | null;
  legado: boolean;
  quantidade: number;
  saldo_lote_resultante: number;
}

export interface MovimentacaoEstoqueExtrato extends MovimentacaoEstoque {
  inventario_id: number | null;
  alocacoes_lote: AlocacaoLoteMovimentacao[];
}

export type TipoOrigemLote =
  | 'FORNECEDOR'
  | 'CARGA_INICIAL'
  | 'INVENTARIO'
  | 'LEGADO'
  | 'NAO_IDENTIFICADA';

export interface OrigemLote {
  tipo: TipoOrigemLote;
  descricao: string;
  movimentacao_id: number | null;
  data_hora: string | null;
  quantidade_origem: number | null;
  ordem_codigo: string | null;
  fornecedor_nome: string | null;
  empenho_codigo: string | null;
  ata_numero: string | null;
  inventario_id: number | null;
}

export interface HistoricoMovimentacaoLote {
  movimentacao_id: number;
  data_hora: string;
  tipo: string;
  tipo_descricao: string;
  sentido: 'E' | 'S';
  quantidade_movimentacao: number;
  quantidade_lote: number;
  saldo_estoque_resultante: number;
  saldo_lote_resultante: number;
  observacao: string | null;
  usuario_nome: string;
  papel: string;
  ordem_codigo: string | null;
  fornecedor_nome: string | null;
  cardapio_id: number | null;
  inventario_id: number | null;
  movimentacao_estornada_id: number | null;
}

export interface RastreabilidadeLote {
  lote: LoteValidade;
  origem: OrigemLote;
  movimentacoes: HistoricoMovimentacaoLote[];
}

export interface EstoqueConsolidado {
  empenho_id: number;
  empenho: string;
  item_generico_id: number;
  catmat: string;
  descricao: string;
  unidade_medida: string;
  categoria: string;
  imagem: string | null;
  saldo_ata: number;
  saldo_empenho: number;
  saldo_estoque: number;
}

export interface LoteRecebimento {
  numero_lote: string;
  data_validade: string;
  quantidade: number;
}

export interface ItemRecebimento {
  item_ordem_id: number;
  lotes: LoteRecebimento[];
  observacao?: string;
}

