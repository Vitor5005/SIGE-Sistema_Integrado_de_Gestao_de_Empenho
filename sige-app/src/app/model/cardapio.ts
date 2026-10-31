import type { StatusValidade } from './estoque';

export type RefeicaoCardapio = 'CAFE' | 'ALMOCO' | 'JANTAR';

export type StatusCardapio =
  | 'RASCUNHO'
  | 'ENVIADO'
  | 'RECUSADO'
  | 'APROVADO'
  | 'CONSUMO_INFORMADO'
  | 'FINALIZADO'
  | 'ALTERACAO_SOLICITADA'
  | 'SUBSTITUIDO';

export const REFEICOES: { valor: RefeicaoCardapio; label: string }[] = [
  { valor: 'CAFE', label: 'Café da manhã' },
  { valor: 'ALMOCO', label: 'Almoço' },
  { valor: 'JANTAR', label: 'Jantar' },
];

export interface ItemCardapio {
  id?: number;
  ordem: number;
  secao: string;
  item_generico: number;
  descricao?: string;
  catmat?: string;
  unidade_medida?: string;
  conteudo_embalagem?: number | null;
  unidade_embalagem?: string | null;
  quantidade_planejada: number | string;
  quantidade_liberada?: number | string | null;
  quantidade_consumida?: number | string | null;
  observacao: string;
}

export interface Cardapio {
  id: number;
  refeicao: RefeicaoCardapio;
  refeicao_descricao: string;
  data: string;
  estimativa_pessoas: number;
  preparacoes: string;
  observacoes: string;
  status: StatusCardapio;
  status_descricao: string;
  motivo_recusa: string;
  motivo_alteracao: string;
  itens: ItemCardapio[];
  criado_por_nome: string;
  criado_em: string;
  atualizado_em: string;
  enviado_em: string | null;
  aprovado_por_nome: string | null;
  aprovado_em: string | null;
  consumo_informado_em: string | null;
  finalizado_por_nome: string | null;
  finalizado_em: string | null;
  /** Rascunho criado quando o estoque aceitou a alteração deste cardápio. */
  substituido_por: number | null;
  /** Cardápio original, quando este rascunho nasceu de uma alteração aceita. */
  substitui: number | null;
}

export interface CardapioResumo {
  id: number;
  refeicao: RefeicaoCardapio;
  refeicao_descricao: string;
  data: string;
  estimativa_pessoas: number;
  status: StatusCardapio;
  status_descricao: string;
  motivo_recusa: string;
  motivo_alteracao: string;
  criado_por_nome: string;
  total_itens: number;
  atualizado_em: string;
}

export interface CardapioInsert {
  refeicao: RefeicaoCardapio | '';
  data: string;
  estimativa_pessoas: number | null;
  preparacoes: string;
  observacoes: string;
  itens: ItemCardapio[];
}

export interface LotePrioritarioCardapio {
  id: number;
  numero_lote: string;
  data_validade: string;
  dias_para_validade: number;
  status: StatusValidade;
  status_descricao: string;
  quantidade_disponivel: number;
}

export interface DisponibilidadeGenero {
  item_generico_id: number;
  catmat: string;
  descricao: string;
  unidade_medida: string;
  categoria: string;
  categoria_descricao: string;
  imagem: string | null;
  conteudo_embalagem: number | null;
  unidade_embalagem: string | null;
  saldo_atual: number;
  saldo_utilizavel: number;
  reservado: number;
  disponivel: number;
  quantidade_prioritaria: number;
  lotes_prioritarios: LotePrioritarioCardapio[];
  proxima_validade: string | null;
  dias_para_proxima_validade: number | null;
  status_proxima_validade: StatusValidade | null;
  status_proxima_validade_descricao: string | null;
}

export interface QuantidadeItemCardapio {
  item: number;
  quantidade: number | string;
}
