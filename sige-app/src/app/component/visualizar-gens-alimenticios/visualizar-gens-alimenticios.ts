import { Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { RouterLink, RouterModule } from '@angular/router';

@Component({
  selector: 'app-visualizar-gens-alimenticios',
  imports: [BarraPesquisa, RouterLink, RouterModule],
  templateUrl: './visualizar-gens-alimenticios.html',
  styleUrl: './visualizar-gens-alimenticios.scss',
})
export class VisualizarGensAlimenticios {

}
