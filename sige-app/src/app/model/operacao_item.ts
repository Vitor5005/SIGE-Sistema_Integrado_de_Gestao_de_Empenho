import { ItemEmpenho } from "./itemEmpenho";

export type OperacaoItem = {
    id: number;
    item_empenho: ItemEmpenho;
    tipo: string;
    valor: number;
    data: Date;
}