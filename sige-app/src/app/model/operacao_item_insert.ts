import { ItemEmpenho } from "./itemEmpenho";

export type OperacaoItemInsert = {
    id: number;
    item_empenho: number;
    tipo: string;
    valor: number;
    data: string;
}