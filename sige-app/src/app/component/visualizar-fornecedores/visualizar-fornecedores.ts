import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';

@Component({
  selector: 'app-visualizar-fornecedores',
  imports: [BarraPesquisa],
  templateUrl: './visualizar-fornecedores.html',
  styleUrl: './visualizar-fornecedores.scss',
})
export class VisualizarFornecedores {

  constructor(private router: Router) { }

  enviarPara(rota: string) {
    this.router.navigate([rota]);
  }

}
