import { ItemEmpenho } from "./itemEmpenho";
import { OrdemEntrega } from "./ordem_entrega"

export type ItemOrdem = {
    id: number;
    ordem_entrega: OrdemEntrega;
    item_empenho: ItemEmpenho; 
    quantidade_solicitada: number;
    quantidade_entregue: number;
    quantidade_pendente?: number;
    observacao?: string | null;
}
