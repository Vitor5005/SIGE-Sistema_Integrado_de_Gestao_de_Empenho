import { Fornecedor } from "./fornecedor";
import { Licitacao } from "./licitacao";

export type Ata = {
    id: number;
    numero_ata: string;
    ata_saldo_total: number;
    licitacao: Licitacao;
    fornecedor: Fornecedor;
}