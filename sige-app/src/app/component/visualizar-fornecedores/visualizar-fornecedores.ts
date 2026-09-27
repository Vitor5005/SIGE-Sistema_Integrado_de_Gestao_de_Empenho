import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Paginacao } from '../utils/paginacao/paginacao';
import { FornecedorService } from '../../service/fornecedor.service';
import { Fornecedor } from '../../model/fornecedor';
import { CommonModule, JsonPipe } from '@angular/common';
import { EstadoConteudo } from '../utils/estado-conteudo/estado-conteudo';
import { EstadoListagemService } from '../../service/estado-listagem.service';
import { FiltroConfig } from './../../model/filtro-config';

@Component({
  selector: 'app-visualizar-fornecedores',
  standalone: true,
  imports: [CommonModule, BarraPesquisa, Paginacao, EstadoConteudo],
  templateUrl: './visualizar-fornecedores.html',
  styleUrl: './visualizar-fornecedores.scss',
})
export class VisualizarFornecedores {

  constructor(
    private router: Router,
    private fornecedorService: FornecedorService,
    private estadoListagem: EstadoListagemService,
  ) { }

  fornecedores = Array<Fornecedor>()
  currentPage: number = 1;
  pageSize: number = 5;
  total: number = 0;
  hasNext: boolean = false;
  hasPrev: boolean = false;
  termoBuscaAtual: string = '';
  filtrosAtivos: Record<string, unknown> = {};
  filtros: FiltroConfig[] = [
    {
      campo: 'endereco__estado',
      label: 'Estado',
      tipo: 'select',
      opcoes: [
        { valor: 'AC', label: 'Acre' },
        { valor: 'AL', label: 'Alagoas' },
        { valor: 'AP', label: 'Amapá' },
        { valor: 'AM', label: 'Amazonas' },
        { valor: 'BA', label: 'Bahia' },
        { valor: 'CE', label: 'Ceará' },
        { valor: 'DF', label: 'Distrito Federal' },
        { valor: 'ES', label: 'Espírito Santo' },
        { valor: 'GO', label: 'Goiás' },
        { valor: 'MA', label: 'Maranhão' },
        { valor: 'MT', label: 'Mato Grosso' },
        { valor: 'MS', label: 'Mato Grosso do Sul' },
        { valor: 'MG', label: 'Minas Gerais' },
        { valor: 'PA', label: 'Pará' },
        { valor: 'PB', label: 'Paraíba' },
        { valor: 'PR', label: 'Paraná' },
        { valor: 'PE', label: 'Pernambuco' },
        { valor: 'PI', label: 'Piauí' },
        { valor: 'RJ', label: 'Rio de Janeiro' },
        { valor: 'RN', label: 'Rio Grande do Norte' },
        { valor: 'RS', label: 'Rio Grande do Sul' },
        { valor: 'RO', label: 'Rondônia' },
        { valor: 'RR', label: 'Roraima' },
        { valor: 'SC', label: 'Santa Catarina' },
        { valor: 'SP', label: 'São Paulo' },
        { valor: 'SE', label: 'Sergipe' },
        { valor: 'TO', label: 'Tocantins' },
      ],
    },
  ];
  isLoadingPage: boolean = false;
  errorMessagePage: string = '';
  private readonly chaveEstadoListagem = 'fornecedores';

  ngOnInit(){
    this.restaurarEstadoListagem();
    this.get()

  }

  enviarPara(rota: string, id?: number) {
    this.salvarEstadoListagem();

    if (id) {
      this.router.navigate([rota], { queryParams: { id } });
    } else {
      this.router.navigate([rota]);
    }
  }

  get(termobusca?: string): void {
    if (termobusca !== undefined) {
      this.termoBuscaAtual = termobusca;
      this.currentPage = 1;
    }

    this.isLoadingPage = true;
    this.errorMessagePage = '';
    this.salvarEstadoListagem();

    this.fornecedorService.get(this.termoBuscaAtual, this.currentPage, this.pageSize, this.filtrosAtivos).subscribe({
      next: (resposta) => {
        this.fornecedores = resposta.results;
        this.total = resposta.count;
        this.hasNext = Boolean(resposta.next);
        this.hasPrev = Boolean(resposta.previous);
        this.isLoadingPage = false;
      },
      error: () => {
        this.isLoadingPage = false;
        this.errorMessagePage = 'Não foi possível carregar os fornecedores no momento.';
      }
    });
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

  aplicarFiltros(filtros: Record<string, unknown>): void {
    this.filtrosAtivos = filtros;
    this.currentPage = 1;
    this.salvarEstadoListagem();
    this.get();
  }

  private restaurarEstadoListagem(): void {
    const estado = this.estadoListagem.obter(this.chaveEstadoListagem);

    if (!estado) {
      return;
    }

    this.termoBuscaAtual = estado.termoBuscaAtual || '';
    this.filtrosAtivos = estado.filtrosAtivos || {};
    this.currentPage = estado.currentPage || 1;
  }

  private salvarEstadoListagem(): void {
    this.estadoListagem.salvar(this.chaveEstadoListagem, {
      termoBuscaAtual: this.termoBuscaAtual,
      filtrosAtivos: this.filtrosAtivos,
      currentPage: this.currentPage,
    });
  }

}
