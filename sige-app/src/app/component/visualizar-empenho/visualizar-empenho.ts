import { Component, ElementRef, ViewChild } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { BotaoVoltar } from '../utils/botao-voltar/botao-voltar';

@Component({
  selector: 'app-visualizar-empenho',
  imports: [RouterLink,BotaoVoltar],
  templateUrl: './visualizar-empenho.html',
  styleUrl: './visualizar-empenho.scss',
})
export class VisualizarEmpenho {

  constructor(private router: Router){}

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild('myInput') input!: ElementRef;

  enviarPara(rota: string) {
    this.router.navigate([rota]);
  }

  ngAfterViewInit() {

    const modalElement = this.modal.nativeElement;

    modalElement.addEventListener('shown.bs.modal', () => {
      this.input.nativeElement.focus();
    });

  }


}
