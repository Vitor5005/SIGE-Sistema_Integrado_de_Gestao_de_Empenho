import { Ata } from "./ata";
import { ItemGenerico } from "./item_generico";

export type ItemAtaInsert = {
    id: number;
    ata: number;
    item_generico: number;
    marca: string;
    quantidade_licitada: number;
    valor_unitario: number;
}