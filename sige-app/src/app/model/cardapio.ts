export type RefeicaoCardapio = 'CAFE' | 'ALMOCO' | 'JANTAR';

export type StatusCardapio =
  | 'RASCUNHO'
  | 'ENVIADO'
  | 'RECUSADO'
  | 'APROVADO'
  | 'CONSUMO_INFORMADO'
  | 'FINALIZADO';

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

export interface DisponibilidadeGenero {
  item_generico_id: number;
  catmat: string;
  descricao: string;
  unidade_medida: string;
  categoria: string;
  conteudo_embalagem: number | null;
  unidade_embalagem: string | null;
  saldo_atual: number;
  reservado: number;
  disponivel: number;
}

export interface QuantidadeItemCardapio {
  item: number;
  quantidade: number | string;
}
