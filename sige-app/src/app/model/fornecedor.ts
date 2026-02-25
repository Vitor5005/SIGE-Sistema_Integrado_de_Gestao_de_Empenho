import { Endereco } from "./endereco";

export type Fornecedor = {
    id: number;
    razao_social: string;
    nome_fantasia: string;
    cnpj: string;
    telefone: string;
    email: string;
    endereco: Endereco;
}