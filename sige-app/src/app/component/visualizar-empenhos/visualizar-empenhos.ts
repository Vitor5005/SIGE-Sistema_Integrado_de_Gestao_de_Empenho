import { FiltroConfig } from './../../model/filtro-config';
import { Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Paginacao } from '../utils/paginacao/paginacao';
import { Router } from '@angular/router';
import { EmpenhoService } from '../../service/empenho.service';
import { Empenho } from '../../model/empenho';

@Component({
  selector: 'app-visualizar-empenhos',
  standalone: true,
  imports: [BarraPesquisa, Paginacao],
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
  currentPage: number = 1;
  pageSize: number = 5;
  total: number = 0;
  hasNext: boolean = false;
  hasPrev: boolean = false;
  termoBuscaAtual: string = '';

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
  if (termobusca !== undefined) {
    this.termoBuscaAtual = termobusca;
    this.currentPage = 1;
  }

  this.empenhoService.get(this.termoBuscaAtual, this.currentPage, this.pageSize, this.filtrosAtivos).subscribe({
    next: (resposta) => {
      this.empenhos = resposta.results || [];
      this.total = resposta.count;
      this.hasNext = Boolean(resposta.next);
      this.hasPrev = Boolean(resposta.previous);
    }
  });
}
  aplicarFiltros(filtros: any) {
  this.filtrosAtivos = filtros;
  this.currentPage = 1;
  this.get();
}

  proximaPagina(): void {
    if (!this.hasNext) {
      return;
    }

    this.currentPage += 1;
    this.get();
  }

  paginaAnterior(): void {
    if (!this.hasPrev || this.currentPage === 1) {
      return;
    }

    this.currentPage -= 1;
    this.get();
  }

  irParaPagina(page: number): void {
    if (page === this.currentPage) {
      return;
    }

    this.currentPage = page;
    this.get();
  }
}
