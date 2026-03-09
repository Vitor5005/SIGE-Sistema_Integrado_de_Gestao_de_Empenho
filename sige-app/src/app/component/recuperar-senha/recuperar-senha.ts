import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { RouterLink } from "@angular/router";

@Component({
  selector: 'app-recuperar-senha',
  imports: [CommonModule, RouterLink],
  templateUrl: './recuperar-senha.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  styleUrl: './recuperar-senha.scss',
})
export class RecuperarSenha {
   etapa = signal<'email' | 'codigo'>('email');

  // Muda para a tela de inserção de código
  irParaCodigo(): void {
    this.etapa.set('codigo');
  }

  // Ação final (apenas log para demonstração)
  finalizar(): void {
    console.log('Processo de verificação concluído.');
  }
}
