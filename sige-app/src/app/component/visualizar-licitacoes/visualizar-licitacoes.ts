import { Component } from '@angular/core';
import { Navegacao } from '../../service/utils/navegacao';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';

@Component({
  selector: 'app-licitacoes',
  imports: [BarraPesquisa],
  templateUrl: './visualizar-licitacoes.html',
  styleUrl: './visualizar-licitacoes.scss',
})
export class VisualizarLicitacoes {
  
  constructor(public navegacao: Navegacao) {}

  enviarPara(rota: string){
    this.navegacao.enviarPara(rota);
  }

}
