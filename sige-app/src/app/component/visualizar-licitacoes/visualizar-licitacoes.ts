import { FiltroConfig } from './../../model/filtro-config';
import { ChangeDetectorRef, Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Paginacao } from '../utils/paginacao/paginacao';
import { Router } from '@angular/router';
import { Licitacao } from '../../model/licitacao';
import { LicitacaoService } from '../../service/licitacao.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-licitacoes',
  imports: [BarraPesquisa, CommonModule, Paginacao],
  templateUrl: './visualizar-licitacoes.html',
  styleUrl: './visualizar-licitacoes.scss',
})
export class VisualizarLicitacoes {
  constructor(
    private router: Router,
    private licitacaoService: LicitacaoService,
  ) {}

  registro: Licitacao[] = [];
  currentPage: number = 1;
  pageSize: number = 5;
  total: number = 0;
  hasNext: boolean = false;
  hasPrev: boolean = false;
  termoBuscaAtual: string = '';

  filtros: FiltroConfig[] = [
  {
      campo: 'status',
      label: 'Status',
      tipo: 'radio',
      opcoes: [
        { valor: 'Válido', label: 'Válido' },
        { valor: 'Expirado', label: 'Expirado' },
      ],
  },
  {
    campo: 'data_abertura',
    label: 'Data de abertura',
    tipo: 'date-range'
  },
];
  filtrosAtivos: any = {};

  ngOnInit() {
    this.get();
    this.filtrosAtivos = {};
  }

  get(termobusca?: string): void {
  if (termobusca !== undefined) {
    this.termoBuscaAtual = termobusca;
    this.currentPage = 1;
  }

  const filtrosParaEnvio = {
    ...this.filtrosAtivos,
    page: this.currentPage,
    page_size: this.pageSize,
    search: this.termoBuscaAtual,
  };

  delete filtrosParaEnvio.status;

  this.licitacaoService.getComFiltros(filtrosParaEnvio).subscribe({
    next: (resposta) => {

      let dados = resposta.results || [];

      // FILTRO DE STATUS
      if (this.filtrosAtivos.status) {
        dados = dados.filter(item =>
          this.verificarValidade(item) === this.filtrosAtivos.status
        );
      }

      this.registro = this.ordenarLicitacoes(dados);

      this.total = resposta.count;
      this.hasNext = Boolean(resposta.next);
      this.hasPrev = Boolean(resposta.previous);
    },
  });
}

  getOrdenadoValidade(): void {
    this.licitacaoService.get().subscribe({
      next: (resposta) => {
        this.registro = this.ordenarLicitacoes(resposta.results);
      },
    });
  }

  enviarPara(rota: string, id: number): void {
    this.router.navigate([rota], { queryParams: { id } });
  }

  aplicarFiltros(filtrosAtivos: any) {
  this.filtrosAtivos = filtrosAtivos || {};
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

  verificarValidade(licitacao: Licitacao): string {
    const dataAtual = new Date();
    const dataAbertura = new Date(licitacao.data_abertura);
    const validade = licitacao.validade;
    const dataExpiracao = new Date(dataAbertura);
    dataExpiracao.setMonth(dataExpiracao.getMonth() + Number(validade));
    if (dataAtual > dataExpiracao) {
      return 'Expirado';
    } else {
      return 'Válido';
    }
  }

  classValidade(licitacao: Licitacao): string {
    if (this.verificarValidade(licitacao) === 'Expirado') {
      return 'bg-danger text-white';
    } else {
      return 'bg-success text-white';
    }
  }

  ordenarLicitacoes(licitacoes: Licitacao[]): Licitacao[] {
    const dataAtual = new Date();

    return licitacoes.sort((a, b) => {
      const dataAberturaA = new Date(a.data_abertura);
      const dataExpiracaoA = new Date(dataAberturaA);
      dataExpiracaoA.setMonth(dataExpiracaoA.getMonth() + Number(a.validade));
      const validaA = dataAtual <= dataExpiracaoA;

      const dataAberturaB = new Date(b.data_abertura);
      const dataExpiracaoB = new Date(dataAberturaB);
      dataExpiracaoB.setMonth(dataExpiracaoB.getMonth() + Number(b.validade));
      const validaB = dataAtual <= dataExpiracaoB;

      // válidas primeiro
      if (validaA && !validaB) return -1;
      if (!validaA && validaB) return 1;

      // ordenar por data (mais recente primeiro)
      return dataAberturaB.getTime() - dataAberturaA.getTime();
    });
  }
}
