import { Component } from '@angular/core';
import { Navegacao } from '../../service/utils/navegacao';

@Component({
  selector: 'app-licitacoes',
  imports: [],
  templateUrl: './visualizar-licitacoes.html',
  styleUrl: './visualizar-licitacoes.scss',
})
export class VisualizarLicitacoes {
  
  constructor(public navegacao: Navegacao) {}

  enviarPara(rota: string){
    this.navegacao.enviarPara(rota);
  }

}
