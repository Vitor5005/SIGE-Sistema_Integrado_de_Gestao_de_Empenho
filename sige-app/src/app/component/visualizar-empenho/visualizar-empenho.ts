import { Component, ElementRef, ViewChild } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { BotaoVoltar } from '../utils/botao-voltar/botao-voltar';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-visualizar-empenho',
  imports: [BotaoVoltar, CommonModule],
  templateUrl: './visualizar-empenho.html',
  styleUrl: './visualizar-empenho.scss',
})
export class VisualizarEmpenho {
  tipo: 'reforco' | 'anulacao'  = 'reforco';
  constructor(private router: Router){}

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild('myInput') input!: ElementRef;

  enviarPara(rota: string) {
    this.router.navigate([rota]);
  }
  prepararOperacao(tipoOperacao: 'reforco' | 'anulacao') {
    this.tipo = tipoOperacao;
  }

  ngAfterViewInit() {

    const modalElement = this.modal.nativeElement;

    modalElement.addEventListener('shown.bs.modal', () => {
      this.input.nativeElement.focus();
    });

  }


}
