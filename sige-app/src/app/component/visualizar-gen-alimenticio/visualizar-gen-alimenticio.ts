import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { BotaoVoltar } from '../utils/botao-voltar/botao-voltar';
import { Acao, pode, Recurso } from '../../security/rbac';

@Component({
  selector: 'app-visualizar-gen-alimenticio',
  imports: [BotaoVoltar, RouterLink],
  templateUrl: './visualizar-gen-alimenticio.html',
  styleUrl: './visualizar-gen-alimenticio.scss',
})
export class VisualizarGenAlimenticio {
   readonly pode = pode;
   readonly Acao = Acao;
   readonly Recurso = Recurso;
   editando = false;

    habilitarEdicao(){
    this.editando = !this.editando;
  }

}

