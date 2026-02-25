import { Empenho } from "./empenho";
import { ItemAta } from "./itemAta";

export type ItemEmpenho = {

    id: number;
    empenho: Empenho;
    item_ata: ItemAta;
    quantidade_atual: number;

}