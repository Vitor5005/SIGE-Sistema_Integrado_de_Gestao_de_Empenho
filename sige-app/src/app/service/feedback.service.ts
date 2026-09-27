import { Injectable, signal } from '@angular/core';

export type FeedbackTipo = 'success' | 'error' | 'warning' | 'info';

export interface FeedbackToast {
  id: number;
  tipo: FeedbackTipo;
  mensagem: string;
  titulo?: string;
}

export interface FeedbackConfirmacao {
  titulo: string;
  mensagem: string;
  textoConfirmar?: string;
  textoCancelar?: string;
  destrutiva?: boolean;
}

@Injectable({ providedIn: 'root' })
export class FeedbackService {
  readonly toasts = signal<FeedbackToast[]>([]);
  readonly confirmacaoAtiva = signal<FeedbackConfirmacao | null>(null);

  private proximoId = 0;
  private resolverConfirmacao: ((resultado: boolean) => void) | null = null;

  sucesso(mensagem: string, titulo?: string): void {
    this.adicionarToast('success', mensagem, titulo);
  }

  erro(mensagem: string, titulo?: string): void {
    this.adicionarToast('error', mensagem, titulo);
  }

  aviso(mensagem: string, titulo?: string): void {
    this.adicionarToast('warning', mensagem, titulo);
  }

  info(mensagem: string, titulo?: string): void {
    this.adicionarToast('info', mensagem, titulo);
  }

  removerToast(id: number): void {
    this.toasts.update((toasts) => toasts.filter((toast) => toast.id !== id));
  }

  confirmar(opcoes: FeedbackConfirmacao): Promise<boolean> {
    if (this.confirmacaoAtiva() || this.resolverConfirmacao) {
      return Promise.resolve(false);
    }

    this.confirmacaoAtiva.set({
      ...opcoes,
      textoConfirmar: opcoes.textoConfirmar || 'Confirmar',
      textoCancelar: opcoes.textoCancelar || 'Cancelar'
    });

    return new Promise<boolean>((resolve) => {
      this.resolverConfirmacao = resolve;
    });
  }

  responderConfirmacao(resultado: boolean): void {
    const resolver = this.resolverConfirmacao;

    this.resolverConfirmacao = null;
    this.confirmacaoAtiva.set(null);
    resolver?.(resultado);
  }

  private adicionarToast(tipo: FeedbackTipo, mensagem: string, titulo?: string): void {
    const toast: FeedbackToast = {
      id: ++this.proximoId,
      tipo,
      mensagem,
      titulo
    };

    this.toasts.update((toasts) => [...toasts, toast]);

    const duracao = tipo === 'success' || tipo === 'info' ? 4000 : 6000;
    setTimeout(() => this.removerToast(toast.id), duracao);
  }
}
