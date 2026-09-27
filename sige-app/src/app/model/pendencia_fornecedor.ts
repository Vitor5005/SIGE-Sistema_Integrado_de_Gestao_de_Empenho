export type StatusPendencia = 'ABERTA' | 'CIENTE' | 'RESOLVIDA';

export type PendenciaFornecedor = {
  id: number;
  status: StatusPendencia;
  quantidade_pendente: number;
  motivo: string;
  ordem_id: number;
  ordem_codigo: string;
  empenho_codigo: string;
  fornecedor: string;
  genero: string;
  unidade_medida: string;
  quantidade_solicitada: number;
  quantidade_entregue: number;
  registrada_por: number;
  registrada_por_nome: string;
  destinatario: number | null;
  destinatario_nome: string | null;
  ciente_por: number | null;
  ciente_por_nome: string | null;
  data_registro: string;
  data_atualizacao: string;
  data_ciencia: string | null;
  data_resolucao: string | null;
};
