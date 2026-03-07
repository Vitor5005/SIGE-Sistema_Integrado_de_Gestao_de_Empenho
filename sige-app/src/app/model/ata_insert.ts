import { Fornecedor } from "./fornecedor";
import { Licitacao } from "./licitacao";

export type AtaInsert = {
    id: number;
    numero_ata: string;
    ata_saldo_total: number;
    licitacao: number;
    fornecedor: number;
}