import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { MovimentacaoEstoque, MovimentacaoEstoqueExtrato } from '../../../model/estoque';
import { EstoqueService } from '../../../service/estoque.service';
import { Acao, pode, Recurso } from '../../../security/rbac';
import { RastreabilidadeLote } from '../rastreabilidade-lote/rastreabilidade-lote';

@Component({
  selector: 'app-extrato-estoque',
  standalone: true,
  imports: [CommonModule, FormsModule, RastreabilidadeLote, RouterLink],
  templateUrl: './extrato-estoque.html',
  styleUrl: '../estoque.scss',
})
export class ExtratoEstoque {
  readonly pode = pode;
  readonly Acao = Acao;
  readonly Recurso = Recurso;

  generoId?: number;
  dataInicio = '';
  dataFim = '';
  loteId?: number;
  loteRastreabilidadeId: number | null = null;
  movimentos: MovimentacaoEstoqueExtrato[] = [];
  movimentosExpandidos = new Set<number>();
  justificativa = '';
  erro = '';
  sucesso = '';

  private readonly tiposMovimentacao: Record<string, string> = {
    ENTRADA_FORNECEDOR: 'Entrada de fornecedor',
    CARGA_INICIAL: 'Carga inicial',
    AJUSTE_POSITIVO: 'Ajuste positivo',
    AJUSTE_NEGATIVO: 'Ajuste negativo',
    SAIDA_PRODUCAO: 'Saída para produção',
    SAIDA_DOACAO: 'Saída para doação',
    SAIDA_PERDA: 'Saída por perda',
    DEVOLUCAO_PREPARO: 'Devolução de sobras do preparo',
    ESTORNO: 'Estorno',
  };

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private estoqueService: EstoqueService,
  ) {}

  ngOnInit(): void {
    const loteId = Number(this.route.snapshot.queryParamMap.get('lote_id'));
    this.loteId = Number.isInteger(loteId) && loteId > 0 ? loteId : undefined;
    this.carregar();
  }

  textoTipoMovimentacao(tipo: string): string {
    return this.tiposMovimentacao[tipo] ?? tipo;
  }

  carregar(): void {
    this.estoqueService.extrato(
      this.generoId,
      this.dataInicio || undefined,
      this.dataFim || undefined,
      this.loteId,
    ).subscribe({
      next: resposta => this.movimentos = resposta.results,
      error: () => this.erro = 'Não foi possível carregar o extrato.',
    });
  }

  alternarDetalhes(movimentoId: number): void {
    if (this.movimentosExpandidos.has(movimentoId)) {
      this.movimentosExpandidos.delete(movimentoId);
    } else {
      this.movimentosExpandidos.add(movimentoId);
    }
  }

  estaExpandida(movimentoId: number): boolean {
    return this.movimentosExpandidos.has(movimentoId);
  }

  abrirRastreabilidade(loteId: number): void {
    this.loteRastreabilidadeId = loteId;
  }

  fecharRastreabilidade(): void {
    this.loteRastreabilidadeId = null;
  }

  limparFiltroLote(): void {
    this.loteId = undefined;
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { lote_id: null },
      queryParamsHandling: 'merge',
    });
    this.carregar();
  }

  descricaoFiltroLote(): string {
    if (!this.loteId) return '';

    for (const movimento of this.movimentos) {
      const alocacao = movimento.alocacoes_lote.find(item => item.lote_id === this.loteId);
      if (alocacao) return `Lote ${alocacao.numero_lote}`;
    }

    return `Lote #${this.loteId}`;
  }

  formatarDataCivil(data: string | null): string {
    if (!data || !/^\d{4}-\d{2}-\d{2}$/.test(data)) return '—';
    const [ano, mes, dia] = data.split('-');
    return `${dia}/${mes}/${ano}`;
  }

  podeEstornarMovimento(movimento: MovimentacaoEstoqueExtrato): boolean {
    return (
      movimento.tipo !== 'ESTORNO'
      && movimento.tipo !== 'AJUSTE_POSITIVO'
      && movimento.tipo !== 'AJUSTE_NEGATIVO'
      && movimento.cardapio_id === null
    );
  }

  estornar(movimento: MovimentacaoEstoque): void {
    const justificativa = prompt('Informe a justificativa obrigatória do estorno:');
    if (!justificativa?.trim()) return;
    this.estoqueService.estornar({ movimentacao_id: movimento.id, justificativa }).subscribe({
      next: () => {
        this.sucesso = 'Movimentação estornada com sucesso.';
        this.carregar();
      },
      error: erro => this.erro = erro.error?.detail || 'Não foi possível estornar a movimentação.',
    });
  }
}

