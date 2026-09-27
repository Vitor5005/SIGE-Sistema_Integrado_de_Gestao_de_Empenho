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
  saldo_atual: number;
  data_atualizacao: string;
}

export interface MovimentacaoEstoque {
  id: number;
  item_generico_id: number;
  genero: string;
  tipo: string;
  sentido: 'E' | 'S';
  quantidade: number;
  saldo_resultante: number;
  data_hora: string;
  observacao: string | null;
  ordem_codigo: string | null;
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
  saldo_ata: number;
  saldo_empenho: number;
  saldo_estoque: number;
}

export interface ItemRecebimento {
  item_ordem_id: number;
  quantidade_recebida: number;
  observacao?: string;
}

