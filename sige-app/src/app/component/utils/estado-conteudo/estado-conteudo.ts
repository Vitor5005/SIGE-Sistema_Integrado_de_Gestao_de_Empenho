import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';

export type EstadoConteudoTipo = 'loading' | 'error' | 'empty';

@Component({
  selector: 'app-estado-conteudo',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './estado-conteudo.html',
  styleUrl: './estado-conteudo.scss'
})
export class EstadoConteudo {
  @Input({ required: true }) tipo!: EstadoConteudoTipo;
  @Input() titulo: string = '';
  @Input() mensagem: string = '';
  @Input() compacto: boolean = false;
  @Input() mostrarAcao: boolean = false;
  @Input() textoAcao: string = 'Tentar novamente';

  @Output() acao = new EventEmitter<void>();

  emitirAcao(): void {
    this.acao.emit();
  }
}
