import { Endereco } from "./endereco";

export type FornecedorInsert = {
    id: number;
    razao_social: string;
    nome_fantasia: string;
    cnpj: string;
    telefone: string;
    email: string;
    endereco: number;
}