import { Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Navegacao } from '../../service/utils/navegacao';

@Component({
  selector: 'app-visualizar-atas',
  imports: [BarraPesquisa],
  templateUrl: './visualizar-atas.html',
  styleUrl: './visualizar-atas.scss',
})
export class VisualizarAtas {

  constructor(private navegacao: Navegacao) {}

  enviarPara(rota: string) {
    this.navegacao.enviarPara(rota);
  }

}
