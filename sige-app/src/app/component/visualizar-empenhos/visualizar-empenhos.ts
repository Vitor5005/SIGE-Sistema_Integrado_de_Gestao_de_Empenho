import { Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Router } from '@angular/router';

@Component({
  selector: 'app-visualizar-empenhos',
  imports: [BarraPesquisa],
  templateUrl: './visualizar-empenhos.html',
  styleUrl: './visualizar-empenhos.scss',
})
export class VisualizarEmpenhos {

  constructor(private router: Router){}

  enviarPara(rota: string){
    this.router.navigate([rota]);
  }

}
