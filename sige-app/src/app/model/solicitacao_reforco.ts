export type StatusSolicitacaoReforco = 'ABERTA' | 'CIENTE';

export interface SolicitacaoReforco {
  id: number;
  status: StatusSolicitacaoReforco;
  item_empenho: number;
  quantidade_solicitada: number;
  empenho_id: number;
  empenho_codigo: string;
  genero: string;
  unidade_medida: string;
  solicitante: number;
  solicitante_nome: string;
  ciente_por: number | null;
  ciente_por_nome: string | null;
  data_solicitacao: string;
  data_ciencia: string | null;
}

export interface SolicitacaoReforcoInsert {
  item_empenho: number;
  quantidade_solicitada: number;
}
