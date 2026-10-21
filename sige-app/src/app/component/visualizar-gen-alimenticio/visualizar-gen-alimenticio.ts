import { Component } from '@angular/core';
import { BotaoVoltar } from '../utils/botao-voltar/botao-voltar';
import { Acao, pode, Recurso } from '../../security/rbac';

@Component({
  selector: 'app-visualizar-gen-alimenticio',
  imports: [BotaoVoltar],
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

