import { Fornecedor } from "./fornecedor";
import { Licitacao } from "./licitacao";

export type Ata = {
    id: number;
    ata_saldo_total: number;
    licitacao: Licitacao;
    fornecedor: Fornecedor;
}