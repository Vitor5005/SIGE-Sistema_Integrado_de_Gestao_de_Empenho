import { Empenho } from "./empenho";

export type OrdemEntregaInsert = {
    id: number;
    empenho: number;
    codigo: string;
    status: string;
    data_emissao: Date;
    data_entrega: Date | null;
    valor_total_executado: number;
}