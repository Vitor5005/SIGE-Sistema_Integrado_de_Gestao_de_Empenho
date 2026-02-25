import { ItemEmpenho } from "./itemEmpenho";
import { OrdemEntrega } from "./ordem_entrega"

export type ItemOrdem = {
    ordem_entrega: OrdemEntrega;
    item_empenho: ItemEmpenho; 
    quantidade_solicitada: number;
    quantidade_entregue: number;
    observacao?: string | null;
}