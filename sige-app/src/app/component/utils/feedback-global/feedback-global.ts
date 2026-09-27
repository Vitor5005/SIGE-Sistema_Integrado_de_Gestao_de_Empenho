import { CommonModule } from '@angular/common';
import { AfterViewInit, Component, DoCheck, ElementRef, ViewChild } from '@angular/core';
import { FeedbackService, FeedbackTipo, FeedbackToast } from '../../../service/feedback.service';

@Component({
  selector: 'app-feedback-global',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './feedback-global.html',
  styleUrl: './feedback-global.scss'
})
export class FeedbackGlobal implements AfterViewInit, DoCheck {
  @ViewChild('dialogConfirmacao') dialogConfirmacao?: ElementRef<HTMLDialogElement>;

  constructor(public readonly feedback: FeedbackService) {}

  ngAfterViewInit(): void {
    this.sincronizarDialog();
  }

  ngDoCheck(): void {
    this.sincronizarDialog();
  }

  removerToast(id: number): void {
    this.feedback.removerToast(id);
  }

  confirmar(): void {
    this.feedback.responderConfirmacao(true);
  }

  cancelar(): void {
    this.feedback.responderConfirmacao(false);
  }

  cancelarDialog(event: Event): void {
    event.preventDefault();
    this.cancelar();
  }

  aoFecharDialog(): void {
    if (this.feedback.confirmacaoAtiva()) {
      this.cancelar();
    }
  }

  aoClicarDialog(event: MouseEvent): void {
    if (event.target === event.currentTarget) {
      this.cancelar();
    }
  }

  tituloToast(toast: FeedbackToast): string {
    if (toast.titulo) {
      return toast.titulo;
    }

    const titulos: Record<FeedbackTipo, string> = {
      success: 'Sucesso',
      error: 'Erro',
      warning: 'Atenção',
      info: 'Informação'
    };

    return titulos[toast.tipo];
  }

  iconeToast(tipo: FeedbackTipo): string {
    const icones: Record<FeedbackTipo, string> = {
      success: 'bi bi-check-circle-fill',
      error: 'bi bi-x-octagon-fill',
      warning: 'bi bi-exclamation-triangle-fill',
      info: 'bi bi-info-circle-fill'
    };

    return icones[tipo];
  }

  private sincronizarDialog(): void {
    const dialog = this.dialogConfirmacao?.nativeElement;

    if (!dialog) {
      return;
    }

    if (this.feedback.confirmacaoAtiva()) {
      if (!dialog.open) {
        dialog.showModal();
      }
      return;
    }

    if (dialog.open) {
      dialog.close();
    }
  }
}
