import { Component } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

@Component({
  selector: 'app-visualizar-licitacao',
  imports: [RouterLink],
  templateUrl: './visualizar-licitacao.html',
  styleUrl: './visualizar-licitacao.scss',
})
export class VisualizarLicitacao {

  constructor(private router: Router) {}

  enviarPara(rota: string) {
    this.router.navigate([rota]);
  }
}
