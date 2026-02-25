import { Empenho } from "./empenho";

export type OrdemEntrega = {
    id: number;
    empenho: Empenho;
    codigo: string;
    status: string;
    data_emissao: Date;
    data_entrega: Date | null;
    valor_total_executado: number;
}