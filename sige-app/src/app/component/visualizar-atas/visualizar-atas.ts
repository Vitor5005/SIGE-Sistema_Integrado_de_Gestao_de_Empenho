import { FiltroConfig } from './../../model/filtro-config';
import { Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Paginacao } from '../utils/paginacao/paginacao';
import { Router } from '@angular/router';
import { AtaService } from '../../service/ata.service';
import { Ata } from '../../model/ata';
import { CommonModule } from '@angular/common';
import { EstadoConteudo } from '../utils/estado-conteudo/estado-conteudo';
import { EstadoListagemService } from '../../service/estado-listagem.service';

@Component({
  selector: 'app-visualizar-atas',
  standalone: true,
  imports: [BarraPesquisa, CommonModule, Paginacao, EstadoConteudo],
  templateUrl: './visualizar-atas.html',
  styleUrl: './visualizar-atas.scss',
})
export class VisualizarAtas {
  constructor(private router: Router, private ataService: AtaService,
    private estadoListagemService: EstadoListagemService,
  ) {}

  atas: Ata[] = [];
  currentPage: number = 1;
  pageSize: number = 5;
  total: number = 0;
  hasNext: boolean = false;
  hasPrev: boolean = false;
  termoBuscaAtual: string = '';
  isLoadingPage: boolean = false;
  errorMessagePage: string = '';

  filtros: FiltroConfig[] = [
    {
      campo: 'ata_saldo_total',
      label: 'Saldo da ARP',
      tipo: 'range',
    },
    {
      campo: 'status',
      label: 'Status',
      tipo: 'radio',
      opcoes: [
        { valor: 'Válido', label: 'Válido' },
        { valor: 'Expirado', label: 'Expirado' },
      ],
    },
  ];

  filtrosAtivos: any = {};

  ngOnInit() {
    this.restaurarEstadoListagem();
    this.get();
  }

  private restaurarEstadoListagem(): void {
    const estado = this.estadoListagemService.obter('atas');

    if (!estado) {
      return;
    }

    this.termoBuscaAtual = estado.termoBuscaAtual || '';
    this.filtrosAtivos = estado.filtrosAtivos || {};
    this.currentPage = estado.currentPage || 1;

    const pageSize = estado.extras?.['pageSize'];
    if (typeof pageSize === 'number' && Number.isInteger(pageSize) && pageSize > 0 && pageSize <= 100) {
      this.pageSize = pageSize;
    }
  }

  private salvarEstadoListagem(): void {
    const estadoAtual = this.estadoListagemService.obter('atas');

    this.estadoListagemService.salvar('atas', {
      termoBuscaAtual: this.termoBuscaAtual,
      filtrosAtivos: this.filtrosAtivos,
      currentPage: this.currentPage,
      extras: {
        ...(estadoAtual?.extras ?? {}),
        pageSize: this.pageSize,
      },
    });
  }

  enviarPara(rota: string, id: number): void {
    this.salvarEstadoListagem();
    this.router.navigate([rota], { queryParams: { id } });
  }

  aplicarFiltros(filtros: any) {
    this.filtrosAtivos = filtros;
    this.currentPage = 1;
    this.salvarEstadoListagem();
    this.get();
  }

  alterarPageSize(pageSize: number): void {
    this.pageSize = pageSize;
    this.currentPage = 1;
    this.salvarEstadoListagem();
    this.get();
  }

 get(termobusca?: string): void {
  if (termobusca !== undefined) {
    this.termoBuscaAtual = termobusca;
    this.currentPage = 1;
    this.salvarEstadoListagem();
  }

  this.isLoadingPage = true;
  this.errorMessagePage = '';

  const status = this.filtrosAtivos.status;
  if (status) {
    this.carregarAtasComFiltroStatus(status);
    return;
  }

  const params = this.montarParametrosFiltro();

  this.ataService.get(params, this.currentPage, this.pageSize).subscribe({
    next: (resposta) => {
      this.atas = this.ordenarAtas(resposta.results || []);
      this.total = resposta.count;
      this.hasNext = Boolean(resposta.next);
      this.hasPrev = Boolean(resposta.previous);
      this.isLoadingPage = false;
    },
    error: () => {
      this.isLoadingPage = false;
      this.errorMessagePage = 'Não foi possível carregar as atas de registro de preços no momento.';
    },
  });
}

  private montarParametrosFiltro(): any {
    const params: any = { ...this.filtrosAtivos };

    if (this.termoBuscaAtual) {
      params.search = this.termoBuscaAtual;
    }

    delete params.status;

    return params;
  }

  private carregarAtasComFiltroStatus(status: string, page: number = 1, acumulados: Ata[] = []): void {
    this.ataService.get(this.montarParametrosFiltro(), page, 100).subscribe({
      next: (resposta) => {
        const registros = [...acumulados, ...(resposta.results || [])];

        if (resposta.next) {
          this.carregarAtasComFiltroStatus(status, page + 1, registros);
          return;
        }

        const filtrados = this.ordenarAtas(registros.filter((ata) => this.verificarValidade(ata) === status));
        this.total = filtrados.length;

        const totalPaginas = Math.max(1, Math.ceil(this.total / this.pageSize));
        if (this.currentPage > totalPaginas) {
          this.currentPage = totalPaginas;
        }

        const inicio = (this.currentPage - 1) * this.pageSize;
        this.atas = filtrados.slice(inicio, inicio + this.pageSize);
        this.hasPrev = this.currentPage > 1;
        this.hasNext = this.currentPage < totalPaginas;
        this.isLoadingPage = false;
      },
      error: () => {
        this.isLoadingPage = false;
        this.errorMessagePage = 'Não foi possível carregar as atas de registro de preços no momento.';
      },
    });
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


  verificarValidade(ata: Ata): string {
    const dataAtual = new Date();
    const dataAbertura = new Date(ata.licitacao.data_abertura);
    const validade = ata.licitacao.validade;

    const dataExpiracao = new Date(dataAbertura);
    dataExpiracao.setMonth(dataExpiracao.getMonth() + Number(validade));

    return dataAtual > dataExpiracao ? 'Expirado' : 'Válido';
  }

  classValidade(ata: Ata): string {
    return this.verificarValidade(ata) === 'Expirado'
      ? 'sige-badge--danger'
      : 'sige-badge--success';
  }

  ordenarAtas(licitacoes: Ata[]): Ata[] {
    const dataAtual = new Date();

    return licitacoes.sort((a, b) => {
      const dataA = new Date(a.licitacao.data_abertura);
      const dataExpA = new Date(dataA);
      dataExpA.setMonth(dataExpA.getMonth() + Number(a.licitacao.validade));

      const dataB = new Date(b.licitacao.data_abertura);
      const dataExpB = new Date(dataB);
      dataExpB.setMonth(dataExpB.getMonth() + Number(b.licitacao.validade));

      const validaA = dataAtual <= dataExpA;
      const validaB = dataAtual <= dataExpB;

      if (validaA && !validaB) return -1;
      if (!validaA && validaB) return 1;

      return dataB.getTime() - dataA.getTime();
    });
  }
}
