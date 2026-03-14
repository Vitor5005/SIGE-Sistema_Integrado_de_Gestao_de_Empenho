import { FiltroConfig } from './../../model/filtro-config';
import { Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Router } from '@angular/router';
import { EmpenhoService } from '../../service/empenho.service';
import { Empenho } from '../../model/empenho';

@Component({
  selector: 'app-visualizar-empenhos',
  imports: [BarraPesquisa],
  templateUrl: './visualizar-empenhos.html',
  styleUrl: './visualizar-empenhos.scss',
})
export class VisualizarEmpenhos {

  filtros: FiltroConfig[] = [
  {
    campo: 'valor_total',
    label: 'Valor empenhado',
    tipo: 'range'
  }
];


filtrosAtivos: any = {};

  constructor(
    private router: Router,
    private empenhoService: EmpenhoService
  ) { }

  empenhos = Array<Empenho>();

  ngOnInit() {
    this.get();
  }

  enviarPara(rota: string, id?: number) {
    if (id) {
      this.router.navigate([rota], { queryParams: { id } });
    }
    else {
      this.router.navigate([rota]);
    }
  }

  get(termobusca?: string): void {

  this.empenhoService.get(termobusca).subscribe({
    next: (resposta: Array<Empenho>) => {
      let lista = resposta || [];

      const min = this.filtrosAtivos.valor_total__gte;
      const max = this.filtrosAtivos.valor_total__lte;

      if (min || max) {
        lista = lista.filter(item => {

          if (min && item.valor_total < Number(min)) return false;
          if (max && item.valor_total > Number(max)) return false;

          return true;
        });
      }
      this.empenhos = lista;
    }
  });
}
  aplicarFiltros(filtros: any) {
  this.filtrosAtivos = filtros;
  this.get();
}
}
