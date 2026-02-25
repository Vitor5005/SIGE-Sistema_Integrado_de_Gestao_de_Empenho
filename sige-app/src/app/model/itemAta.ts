import { Ata } from "./ata";
import { ItemGenerico } from "./item_generico";

export type ItemAta = {
    id: number;
    ata: Ata;
    item_generico: ItemGenerico;
    marca: string;
    quantidade_licitada: number;
    valor_unitario: number;
}