import { Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Router } from '@angular/router';

@Component({
  selector: 'app-visualizar-atas',
  imports: [BarraPesquisa],
  templateUrl: './visualizar-atas.html',
  styleUrl: './visualizar-atas.scss',
})
export class VisualizarAtas {

  constructor(private router: Router) {}

  enviarPara(rota: string) {
    this.router.navigate([rota]);
  }

}
