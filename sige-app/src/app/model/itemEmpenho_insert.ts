import { Empenho } from "./empenho";
import { ItemAta } from "./itemAta";

export type ItemEmpenhoInsert = {

    id: number;
    empenho: number;
    item_ata: number;
    quantidade_atual: number;

}