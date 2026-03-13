import { ItemEmpenho } from "./itemEmpenho";
import { OrdemEntrega } from "./ordem_entrega"

export type ItemOrdemInsert = {
    id: number;
    ordem_entrega: number;
    item_empenho: number; 
    quantidade_solicitada: number;
    quantidade_entregue: number;
    observacao?: string | null;
}
