import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Navegacao } from '../../service/utils/navegacao';

@Component({
  selector: 'app-visualizar-licitacao',
  imports: [RouterLink],
  templateUrl: './visualizar-licitacao.html',
  styleUrl: './visualizar-licitacao.scss',
})
export class VisualizarLicitacao {

  constructor(private navegacao: Navegacao) {}

  enviarPara(rota: string) {
    this.navegacao.enviarPara(rota);
  }
}
