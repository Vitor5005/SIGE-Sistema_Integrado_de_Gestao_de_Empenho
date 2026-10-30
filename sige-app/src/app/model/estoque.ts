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

