export type StatusSolicitacaoReforco = 'PENDENTE' | 'ATENDIDA' | 'RECUSADA';

export type SolicitacaoReforco = {
  id: number;
  item_empenho: number;
  quantidade: number;
  justificativa: string;
  status: StatusSolicitacaoReforco;
  empenho_id: number;
  empenho_codigo: string;
  genero: string;
  unidade_medida: string;
  quantidade_atual_item: number;
  solicitante: number;
  solicitante_nome: string;
  respondida_por: number | null;
  respondida_por_nome: string | null;
  resposta: string;
  operacao: number | null;
  data_solicitacao: string;
  data_resposta: string | null;
  vista_pelo_solicitante: boolean;
};
