import { Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-visualizar-entregas',
  imports: [BarraPesquisa, CommonModule],
  templateUrl: './visualizar-entregas.html',
  styleUrl: './visualizar-entregas.scss',
})
export class VisualizarEntregas {

  confirmado : boolean = false;

}
