import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { FiltroConfig } from '../../model/filtro-config';
import { EstoqueConsolidado, EstoqueItem } from '../../model/estoque';
import { EstoqueService } from '../../service/estoque.service';
import { EstadoListagemService } from '../../service/estado-listagem.service';
import { Acao, pode, Recurso } from '../../security/rbac';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';

@Component({
  selector: 'app-estoque',
  standalone: true,
  imports: [BarraPesquisa, CommonModule, RouterLink],
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
  filtros: FiltroConfig[] = [
    {
      campo: 'item_generico__categoria',
      label: 'Categoria',
      tipo: 'select',
      opcoes: [
        { valor: 'tempS', label: 'Temperos Secos' },
        { valor: 'SM', label: 'Secos / Mercearia' },
        { valor: 'Lac', label: 'Lácteos e Derivados' },
        { valor: 'Oli', label: 'Óleos, Azeites e Vinagres' },
        { valor: 'MolCo', label: 'Molhos e Condimentos' },
        { valor: 'Fr', label: 'Frutas' },
        { valor: 'Le', label: 'Legumes' },
        { valor: 'Pr', label: 'Proteínas' }
      ]
    }
  ];
  agruparPorCategoria = false;
  carregando = false;
  erro = '';

  constructor(
    private estoqueService: EstoqueService,
    private estadoListagem: EstadoListagemService
  ) {}

  ngOnInit(): void {
    this.restaurarEstadoListagem();
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

    const categoria = this.filtrosAtivos['item_generico__categoria'] || '';
    this.carregando = true;
    this.estoqueService.listar(this.termoBuscaAtual, 1, 100, categoria).subscribe({
      next: resposta => {
        this.itens = resposta.results;
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
}

