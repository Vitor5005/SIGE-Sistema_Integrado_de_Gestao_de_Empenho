/** Reforço registrado pelo Diretor que o Técnico ainda não confirmou ter visto. */
export type ReforcoParaPedido = {
  id: number;
  valor: number;
  data: string;
  ciente_tecnico: boolean;
  empenho_id: number;
  empenho_codigo: string;
  fornecedor: string;
  genero: string;
  unidade_medida: string;
};
