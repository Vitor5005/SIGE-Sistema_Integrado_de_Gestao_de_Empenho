import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { FiltroConfig } from '../../model/filtro-config';
import { EstoqueConsolidado, EstoqueItem } from '../../model/estoque';
import { EstoqueService } from '../../service/estoque.service';
import { EstadoListagemService } from '../../service/estado-listagem.service';
import { Acao, pode, Recurso } from '../../security/rbac';
import { DetalhesLotesEstoque } from './detalhes-lotes-estoque/detalhes-lotes-estoque';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';

@Component({
  selector: 'app-estoque',
  standalone: true,
  imports: [BarraPesquisa, CommonModule, DetalhesLotesEstoque, RouterLink],
  templateUrl: './estoque.html',
  styleUrl: './estoque.scss',
})
export class Estoque {
  readonly pode = pode;
  readonly Acao = Acao;
  readonly Recurso = Recurso;

  itens: EstoqueItem[] = [];
  consolidado: EstoqueConsolidado[] = [];
  termoBuscaAtual = '';
  filtrosAtivos: Record<string, any> = {};
  readonly campoCategoria = 'item_generico__categoria';
  readonly categorias = [
    { valor: 'tempS', label: 'Temperos Secos' },
    { valor: 'SM', label: 'Secos / Mercearia' },
    { valor: 'Lac', label: 'Lácteos e Derivados' },
    { valor: 'Oli', label: 'Óleos, Azeites e Vinagres' },
    { valor: 'MolCo', label: 'Molhos e Condimentos' },
    { valor: 'Fr', label: 'Frutas' },
    { valor: 'Le', label: 'Legumes' },
    { valor: 'Pr', label: 'Proteínas' },
  ];
  filtros: FiltroConfig[] = [
    {
      campo: this.campoCategoria,
      label: 'Categoria',
      tipo: 'select',
      opcoes: this.categorias,
    },
  ];
  agruparPorCategoria = false;
  modoVisualizacao: 'cards' | 'tabela' = 'cards';
  imagensComErro = new Set<string>();
  carregando = false;
  erro = '';
  totalItens = 0;
  itemLotesSelecionado: EstoqueItem | null = null;

  get podeVerValidadeEstoquista(): boolean {
    return this.pode(this.Recurso.ESTOQUE, this.Acao.REGISTRAR_SAIDA);
  }

  get podeVerValidadeNutricionista(): boolean {
    return this.pode(this.Recurso.PAINEL_NUTRICIONISTA, this.Acao.CONSULTAR);
  }

  get podeVerIndicadoresValidade(): boolean {
    return this.podeVerValidadeEstoquista || this.podeVerValidadeNutricionista;
  }

  get categoriaSelecionada(): string {
    return String(this.filtrosAtivos[this.campoCategoria] ?? '');
  }

  get temFiltrosAtivos(): boolean {
    return Object.keys(this.filtrosAtivos).some(campo => {
      const valor = this.filtrosAtivos[campo];
      return Array.isArray(valor)
        ? valor.length > 0
        : valor !== null && valor !== undefined && valor !== '';
    });
  }

  get descricaoCategoriaSelecionada(): string {
    return this.categorias.find(categoria => categoria.valor === this.categoriaSelecionada)?.label ?? '';
  }

  constructor(
    private estoqueService: EstoqueService,
    private estadoListagem: EstadoListagemService
  ) {}

  private readonly chaveVisualizacao = 'sige.estoque.visualizacao';

  private readonly iconesCategoria: Record<string, string> = {
    tempS: 'bi-flower2',
    SM: 'bi-box-seam',
    Lac: 'bi-cup-straw',
    Oli: 'bi-droplet',
    MolCo: 'bi-cup-hot',
    Fr: 'bi-basket',
    Le: 'bi-basket2',
    Pr: 'bi-egg-fried',
  };

  ngOnInit(): void {
    this.restaurarEstadoListagem();
    this.restaurarVisualizacao();
    this.carregar();
    if (pode(Recurso.ESTOQUE, Acao.CONSULTAR_CONSOLIDADO)) {
      this.estoqueService.consolidado().subscribe({
        next: dados => this.consolidado = dados,
        error: () => this.erro = 'Não foi possível carregar a visão consolidada.',
      });
    }
  }

  carregar(termobusca?: string): void {
    if (termobusca !== undefined) {
      this.termoBuscaAtual = termobusca;
      this.salvarEstadoListagem();
    }

    const categoria = this.filtrosAtivos[this.campoCategoria] || '';
    this.carregando = true;
    this.estoqueService.listar(this.termoBuscaAtual, 1, 100, categoria).subscribe({
      next: resposta => {
        this.itens = resposta.results;
        this.totalItens = resposta.count;
        if (this.agruparPorCategoria) {
          this.ordenarItensPorCategoria();
        }
        this.carregando = false;
      },
      error: () => {
        this.erro = 'Não foi possível carregar o estoque.';
        this.carregando = false;
      },
    });
  }

  alterarVisualizacao(modo: 'cards' | 'tabela'): void {
    this.modoVisualizacao = modo;
    try {
      localStorage.setItem(this.chaveVisualizacao, modo);
    } catch {
      // Sem acesso ao armazenamento do navegador, a escolha vale só nesta visita.
    }
  }

  alterarCategoria(categoria: string): void {
    const filtros = { ...this.filtrosAtivos };
    if (categoria) {
      filtros[this.campoCategoria] = categoria;
    } else {
      delete filtros[this.campoCategoria];
    }
    this.aplicarFiltros(filtros);
  }

  removerCategoria(): void {
    this.alterarCategoria('');
  }

  limparFiltros(): void {
    this.aplicarFiltros({});
  }

  unidadeComEmbalagem(item: EstoqueItem): string {
    if (!item.conteudo_embalagem || !item.unidade_embalagem) {
      return item.unidade_medida;
    }
    return `${item.unidade_medida} (${item.conteudo_embalagem} ${item.unidade_embalagem})`;
  }

  saldoUtilizavelDiferente(item: EstoqueItem): boolean {
    return Number(item.saldo_utilizavel) !== Number(item.saldo_atual);
  }

  iconeCategoria(categoria: string): string {
    return this.iconesCategoria[categoria] || 'bi-image';
  }

  private restaurarVisualizacao(): void {
    try {
      const salvo = localStorage.getItem(this.chaveVisualizacao);
      if (salvo === 'cards' || salvo === 'tabela') {
        this.modoVisualizacao = salvo;
      }
    } catch {
      this.modoVisualizacao = 'cards';
    }
  }

  alternarAgrupamento(): void {
    this.agruparPorCategoria = !this.agruparPorCategoria;
    if (this.agruparPorCategoria) {
      this.ordenarItensPorCategoria();
    }
    this.salvarEstadoListagem();
  }

  aplicarFiltros(filtros: Record<string, any>): void {
    this.filtrosAtivos = { ...filtros };
    this.salvarEstadoListagem();
    this.carregar();
  }

  salvarEstadoListagem(): void {
    this.estadoListagem.salvar('estoque', {
      termoBuscaAtual: this.termoBuscaAtual,
      filtrosAtivos: this.filtrosAtivos,
      currentPage: 1,
      extras: {
        agruparPorCategoria: this.agruparPorCategoria
      }
    });
  }

  private restaurarEstadoListagem(): void {
    const estado = this.estadoListagem.obter('estoque');
    if (!estado) {
      return;
    }

    this.termoBuscaAtual = estado.termoBuscaAtual;
    this.filtrosAtivos = { ...estado.filtrosAtivos };
    this.agruparPorCategoria = Boolean(estado.extras?.['agruparPorCategoria']);
  }

  private ordenarItensPorCategoria(): void {
    this.itens = [...this.itens].sort((a, b) =>
      a.categoria_descricao.localeCompare(b.categoria_descricao)
      || a.descricao.localeCompare(b.descricao)
    );
  }

  iniciaCategoria(index: number): boolean {
    return this.agruparPorCategoria && (
      index === 0 || this.itens[index - 1].categoria !== this.itens[index].categoria
    );
  }

  abrirLotes(item: EstoqueItem): void {
    if (!this.pode(this.Recurso.ESTOQUE, this.Acao.CONSULTAR)) {
      return;
    }

    this.itemLotesSelecionado = item;
  }

  fecharLotes(): void {
    this.itemLotesSelecionado = null;
  }

  abrirLotesPorTeclado(event: KeyboardEvent, item: EstoqueItem): void {
    if (event.key !== 'Enter' && event.key !== ' ') {
      return;
    }

    event.preventDefault();
    this.abrirLotes(item);
  }

  temValidadePrioritaria(item: EstoqueItem): boolean {
    const proximos = Number(item.lotes_vence_hoje || 0)
      + Number(item.lotes_criticos || 0)
      + Number(item.lotes_atencao || 0);
    return proximos > 0 || (
      this.podeVerValidadeEstoquista && Number(item.lotes_vencidos || 0) > 0
    );
  }

  textoProximaValidade(item: EstoqueItem): string {
    if (!item.proxima_validade || item.dias_para_proxima_validade === null) {
      return '';
    }

    if (item.dias_para_proxima_validade === 0) {
      return 'Próxima validade: hoje';
    }
    if (item.dias_para_proxima_validade === 1) {
      return 'Próxima validade em 1 dia';
    }
    return `Próxima validade em ${item.dias_para_proxima_validade} dias`;
  }

  classeProximaValidade(item: EstoqueItem): string {
    switch (item.status_proxima_validade) {
      case 'VENCE_HOJE':
        return 'text-danger';
      case 'CRITICO':
        return 'text-warning';
      case 'ATENCAO':
        return 'text-info';
      case 'REGULAR':
        return 'text-secondary';
      default:
        return 'text-secondary';
    }
  }
}

