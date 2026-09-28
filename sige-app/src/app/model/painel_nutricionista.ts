export interface DisponibilidadeGenero {
  item_generico_id: number;
  catmat: string;
  descricao: string;
  unidade_medida: string;
  categoria: string;
  categoria_descricao: string;
  em_estoque: number;
  a_caminho: number;
  empenhado: number;
  na_arp: number;
}

export interface SerieMovimentacao {
  entradas: number[];
  saidas: number[];
}

export interface SaldoEmpenho {
  id: number;
  codigo: string;
  fornecedor: string;
  valor_total: number;
  valor_utilizado: number;
  saldo_disponivel: number;
}

export interface SaldoArp {
  id: number;
  numero_ata: string;
  fornecedor: string;
  licitacao: string;
  valor_registrado: number;
  saldo_disponivel: number;
}

export interface PainelNutricionista {
  generos: DisponibilidadeGenero[];
  movimentacao: {
    semanas: string[];
    por_genero: Record<string, SerieMovimentacao>;
  };
  empenhos: SaldoEmpenho[];
  arps: SaldoArp[];
}
