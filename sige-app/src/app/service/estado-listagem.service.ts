import { Injectable } from '@angular/core';

export interface EstadoListagem {
  termoBuscaAtual: string;
  filtrosAtivos: Record<string, any>;
  currentPage: number;
  extras?: Record<string, any>;
}

@Injectable({
  providedIn: 'root'
})
export class EstadoListagemService {
  private readonly estados = new Map<string, EstadoListagem>();

  salvar(chave: string, estado: EstadoListagem): void {
    this.estados.set(chave, this.clonar(estado));
  }

  obter(chave: string): EstadoListagem | null {
    const estado = this.estados.get(chave);
    return estado ? this.clonar(estado) : null;
  }

  limpar(chave: string): void {
    this.estados.delete(chave);
  }

  private clonar<T>(valor: T): T {
    return JSON.parse(JSON.stringify(valor)) as T;
  }
}
