import { Ata } from "./ata";

export type EmpenhoInsert = {

    id: number;
    codigo: string;
    ata: number;
    valor_total: number;
    saldo_utilizado: number;
    quantidade_itens: number;

}