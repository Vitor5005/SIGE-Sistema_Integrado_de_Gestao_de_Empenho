import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { FiltroConfig } from '../../../model/filtro-config';
import { LoteValidade, ResumoValidades, StatusValidade } from '../../../model/estoque';
import { Acao, pode, Recurso } from '../../../security/rbac';
import { EstoqueService } from '../../../service/estoque.service';
import { RastreabilidadeLote } from '../rastreabilidade-lote/rastreabilidade-lote';
import { BarraPesquisa } from '../../utils/barra-pesquisa/barra-pesquisa';
import { Paginacao } from '../../utils/paginacao/paginacao';

type CampoResumoValidade =
  | 'vencidos'
  | 'vence_hoje'
  | 'criticos'
  | 'atencao'
  | 'regulares'
  | 'sem_validade';

interface CardResumoValidade {
  status: StatusValidade;
  label: string;
  campo: CampoResumoValidade;
}

@Component({
  selector: 'app-validades-estoque',
  standalone: true,
  imports: [BarraPesquisa, CommonModule, Paginacao, RastreabilidadeLote, RouterLink],
  templateUrl: './validades-estoque.html',
  styleUrl: '../estoque.scss',
})
export class ValidadesEstoque {
  readonly pode = pode;
  readonly Recurso = Recurso;
  readonly Acao = Acao;

  readonly filtros: FiltroConfig[] = [
    {
      campo: 'categoria',
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
        { valor: 'Pr', label: 'Proteínas' },
      ],
    },
    {
      campo: 'status',
      label: 'Situação da validade',
      tipo: 'select',
      opcoes: [
        { valor: 'VENCIDO', label: 'Vencido' },
        { valor: 'VENCE_HOJE', label: 'Vence hoje' },
        { valor: 'CRITICO', label: 'Crítico — até 7 dias' },
        { valor: 'ATENCAO', label: 'Atenção — 8 a 30 dias' },
        { valor: 'REGULAR', label: 'Regular — mais de 30 dias' },
        { valor: 'SEM_VALIDADE', label: 'Sem validade' },
      ],
    },
    {
      campo: 'data_validade',
      label: 'Período de validade',
      tipo: 'date-range',
    },
  ];

  readonly cardsResumo: CardResumoValidade[] = [
    { status: 'VENCIDO', label: 'Vencidos', campo: 'vencidos' },
    { status: 'VENCE_HOJE', label: 'Vence hoje', campo: 'vence_hoje' },
    { status: 'CRITICO', label: 'Críticos', campo: 'criticos' },
    { status: 'ATENCAO', label: 'Atenção', campo: 'atencao' },
    { status: 'REGULAR', label: 'Regulares', campo: 'regulares' },
    { status: 'SEM_VALIDADE', label: 'Sem validade', campo: 'sem_validade' },
  ];

  lotes: LoteValidade[] = [];
  resumo: ResumoValidades | null = null;
  termoBuscaAtual = '';
  filtrosAtivos: Record<string, any> = {};
  currentPage = 1;
  pageSize = 10;
  total = 0;
  hasNext = false;
  hasPrev = false;
  carregando = false;
  carregandoResumo = false;
  erro = '';
  loteRastreabilidadeId: number | null = null;

  constructor(private estoqueService: EstoqueService) {}

  ngOnInit(): void {
    this.carregarResumo();
    this.carregar();
  }

  carregar(termoBusca?: string): void {
    if (termoBusca !== undefined) {
      this.termoBuscaAtual = termoBusca;
      this.currentPage = 1;
    }

    this.carregando = true;
    this.erro = '';
    this.estoqueService.listarLotesValidade(
      this.termoBuscaAtual,
      this.currentPage,
      this.pageSize,
      this.filtrosAtivos,
    ).subscribe({
      next: resposta => {
        this.lotes = resposta.results;
        this.total = resposta.count;
        this.hasNext = Boolean(resposta.next);
        this.hasPrev = Boolean(resposta.previous);
        this.carregando = false;
      },
      error: () => {
        this.erro = 'Não foi possível carregar os lotes e validades.';
        this.carregando = false;
      },
    });
  }

  carregarResumo(): void {
    this.carregandoResumo = true;
    this.estoqueService.resumoValidades().subscribe({
      next: resumo => {
        this.resumo = resumo;
        this.carregandoResumo = false;
      },
      error: () => {
        this.resumo = null;
        this.carregandoResumo = false;
      },
    });
  }

  aplicarFiltros(filtros: Record<string, any>): void {
    this.filtrosAtivos = { ...filtros };
    this.currentPage = 1;
    this.carregar();
  }

  aplicarStatus(status: StatusValidade): void {
    this.filtrosAtivos = { ...this.filtrosAtivos, status };
    this.currentPage = 1;
    this.carregar();
  }

  irParaPagina(page: number): void {
    this.currentPage = page;
    this.carregar();
  }

  alterarPageSize(pageSize: number): void {
    this.pageSize = pageSize;
    this.currentPage = 1;
    this.carregar();
  }

  abrirRastreabilidade(loteId: number): void {
    this.loteRastreabilidadeId = loteId;
  }

  fecharRastreabilidade(): void {
    this.loteRastreabilidadeId = null;
  }

  valorResumo(campo: CampoResumoValidade): number {
    return this.resumo?.[campo] ?? 0;
  }

  formatarDataCivil(data: string | null): string {
    if (!data || !/^\d{4}-\d{2}-\d{2}$/.test(data)) {
      return '—';
    }

    const [ano, mes, dia] = data.split('-');
    return `${dia}/${mes}/${ano}`;
  }

  prazoValidade(dias: number | null): string {
    if (dias === null || dias === undefined) {
      return '—';
    }

    if (dias < 0) {
      const quantidade = Math.abs(dias);
      return `Vencido há ${quantidade} ${quantidade === 1 ? 'dia' : 'dias'}`;
    }

    if (dias === 0) {
      return 'Hoje';
    }

    return `${dias} ${dias === 1 ? 'dia' : 'dias'}`;
  }

  classeStatus(status: StatusValidade): string {
    switch (status) {
      case 'VENCIDO':
      case 'VENCE_HOJE':
        return 'text-bg-danger';
      case 'CRITICO':
        return 'text-bg-warning';
      case 'ATENCAO':
        return 'text-bg-info';
      case 'REGULAR':
        return 'text-bg-success';
      default:
        return 'text-bg-secondary';
    }
  }
}
