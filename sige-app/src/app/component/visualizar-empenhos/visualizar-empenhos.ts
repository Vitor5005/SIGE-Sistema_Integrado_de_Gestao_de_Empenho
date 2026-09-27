import { FiltroConfig } from './../../model/filtro-config';
import { Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Paginacao } from '../utils/paginacao/paginacao';
import { Router } from '@angular/router';
import { EmpenhoService } from '../../service/empenho.service';
import { Empenho } from '../../model/empenho';
import { EstadoConteudo } from '../utils/estado-conteudo/estado-conteudo';
import { EstadoListagemService } from '../../service/estado-listagem.service';

@Component({
  selector: 'app-visualizar-empenhos',
  standalone: true,
  imports: [BarraPesquisa, Paginacao, EstadoConteudo],
  templateUrl: './visualizar-empenhos.html',
  styleUrl: './visualizar-empenhos.scss',
})
export class VisualizarEmpenhos {

  filtros: FiltroConfig[] = [
  {
    campo: 'valor_total',
    label: 'Valor empenhado',
    tipo: 'range'
  },
  {
    campo: 'saldo_utilizado',
    label: 'Valor utilizado',
    tipo: 'range'
  }
];


filtrosAtivos: any = {};

  constructor(
    private router: Router,
    private empenhoService: EmpenhoService,
    private estadoListagemService: EstadoListagemService,
  ) { }

  empenhos = Array<Empenho>();
  currentPage: number = 1;
  pageSize: number = 5;
  total: number = 0;
  hasNext: boolean = false;
  hasPrev: boolean = false;
  termoBuscaAtual: string = '';
  isLoadingPage: boolean = false;
  errorMessagePage: string = '';

  ngOnInit() {
    this.restaurarEstadoListagem();
    this.get();
  }

  private restaurarEstadoListagem(): void {
    const estado = this.estadoListagemService.obter('empenhos');

    if (!estado) {
      return;
    }

    this.termoBuscaAtual = estado.termoBuscaAtual || '';
    this.filtrosAtivos = estado.filtrosAtivos || {};
    this.currentPage = estado.currentPage || 1;
  }

  private salvarEstadoListagem(): void {
    this.estadoListagemService.salvar('empenhos', {
      termoBuscaAtual: this.termoBuscaAtual,
      filtrosAtivos: this.filtrosAtivos,
      currentPage: this.currentPage,
    });
  }

  enviarPara(rota: string, id?: number) {
    this.salvarEstadoListagem();
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
    this.salvarEstadoListagem();
  }

  this.isLoadingPage = true;
  this.errorMessagePage = '';

  this.empenhoService.get(this.termoBuscaAtual, this.currentPage, this.pageSize, this.filtrosAtivos).subscribe({
    next: (resposta) => {
      this.empenhos = resposta.results || [];
      this.total = resposta.count;
      this.hasNext = Boolean(resposta.next);
      this.hasPrev = Boolean(resposta.previous);
      this.isLoadingPage = false;
    },
    error: () => {
      this.isLoadingPage = false;
      this.errorMessagePage = 'Não foi possível carregar os empenhos no momento.';
    },
  });
}
  aplicarFiltros(filtros: any) {
  this.filtrosAtivos = filtros;
  this.currentPage = 1;
  this.salvarEstadoListagem();
  this.get();
}

  proximaPagina(): void {
    if (!this.hasNext) {
      return;
    }

    this.currentPage += 1;
    this.salvarEstadoListagem();
    this.get();
  }

  paginaAnterior(): void {
    if (!this.hasPrev || this.currentPage === 1) {
      return;
    }

    this.currentPage -= 1;
    this.salvarEstadoListagem();
    this.get();
  }

  irParaPagina(page: number): void {
    if (page === this.currentPage) {
      return;
    }

    this.currentPage = page;
    this.salvarEstadoListagem();
    this.get();
  }
}
