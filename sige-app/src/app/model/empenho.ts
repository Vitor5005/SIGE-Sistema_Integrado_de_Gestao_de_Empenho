import { Ata } from "./ata";

export type Empenho = {

    id: number;
    codigo: string;
    ata: Ata;
    valor_total: number;
    saldo_utilizado: number;
    quantidade_itens: number;

}