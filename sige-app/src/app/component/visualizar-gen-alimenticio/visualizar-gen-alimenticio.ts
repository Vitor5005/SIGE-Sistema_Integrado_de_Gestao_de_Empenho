import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { BotaoVoltar } from '../utils/botao-voltar/botao-voltar';

@Component({
  selector: 'app-visualizar-gen-alimenticio',
  imports: [BotaoVoltar, RouterLink],
  templateUrl: './visualizar-gen-alimenticio.html',
  styleUrl: './visualizar-gen-alimenticio.scss',
})
export class VisualizarGenAlimenticio {
   editando = false;

    habilitarEdicao(){
    this.editando = !this.editando;
  }

}

