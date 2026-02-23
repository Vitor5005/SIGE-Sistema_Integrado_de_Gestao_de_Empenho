import { Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Router } from '@angular/router';

@Component({
  selector: 'app-licitacoes',
  imports: [BarraPesquisa],
  templateUrl: './visualizar-licitacoes.html',
  styleUrl: './visualizar-licitacoes.scss',
})
export class VisualizarLicitacoes {
  
  constructor(private router: Router) {}

  enviarPara(rota: string){
    this.router.navigate([rota]);
  }

}
