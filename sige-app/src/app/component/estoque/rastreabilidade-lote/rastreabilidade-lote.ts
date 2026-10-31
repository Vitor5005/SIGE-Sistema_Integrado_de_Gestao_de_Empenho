import { CommonModule } from '@angular/common';
import { Component, EventEmitter, HostListener, Input, OnChanges, OnDestroy, Output, SimpleChanges } from '@angular/core';
import { RouterLink } from '@angular/router';

import {
  HistoricoMovimentacaoLote,
  RastreabilidadeLote as DadosRastreabilidadeLote,
  StatusValidade,
} from '../../../model/estoque';
import { EstoqueService } from '../../../service/estoque.service';

@Component({
  selector: 'app-rastreabilidade-lote',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './rastreabilidade-lote.html',
  styleUrl: '../estoque.scss',
})
export class RastreabilidadeLote implements OnChanges, OnDestroy {
  @Input() loteId: number | null = null;
  @Input() embutido = false;
  @Output() fechar = new EventEmitter<void>();

  rastreabilidade: DadosRastreabilidadeLote | null = null;
  carregando = false;
  erro = '';
  private overflowBodyAnterior: string | null = null;

  constructor(private estoqueService: EstoqueService) {}

  ngOnChanges(changes: SimpleChanges): void {
    this.sincronizarScrollPagina();
    if (!changes['loteId']) return;

    this.rastreabilidade = null;
    this.erro = '';
    this.carregando = false;

    if (this.loteId !== null && Number.isInteger(this.loteId) && this.loteId > 0) {
      this.carregar(this.loteId);
    }
  }

  ngOnDestroy(): void {
    this.liberarScrollPagina();
  }

  @HostListener('document:keydown.escape')
  aoPressionarEscape(): void {
    if (!this.embutido && this.loteId !== null) this.solicitarFechamento();
  }

  solicitarFechamento(): void {
    this.fechar.emit();
  }

  formatarDataCivil(data: string | null): string {
    if (!data || !/^\d{4}-\d{2}-\d{2}$/.test(data)) return '—';
    const [ano, mes, dia] = data.split('-');
    return `${dia}/${mes}/${ano}`;
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

  referenciaMovimentacao(movimentacao: HistoricoMovimentacaoLote): string {
    if (movimentacao.ordem_codigo) return `Ordem ${movimentacao.ordem_codigo}`;
    if (movimentacao.cardapio_id) return `Cardápio #${movimentacao.cardapio_id}`;
    if (movimentacao.inventario_id) return `Inventário #${movimentacao.inventario_id}`;
    if (movimentacao.movimentacao_estornada_id) {
      return `Movimento estornado #${movimentacao.movimentacao_estornada_id}`;
    }
    return '—';
  }

  formatarQuantidade(quantidade: number | null | undefined): string {
    if (quantidade === null || quantidade === undefined) return '—';
    const valor = Number(quantidade);
    if (!Number.isFinite(valor)) return '—';
    const unidade = this.rastreabilidade?.lote.unidade_medida;
    const texto = valor.toLocaleString('pt-BR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 3,
    });
    return unidade ? `${texto} ${unidade}` : texto;
  }

  private sincronizarScrollPagina(): void {
    const loteValido = this.loteId !== null && Number.isInteger(this.loteId) && this.loteId > 0;
    if (!this.embutido && loteValido) {
      this.bloquearScrollPagina();
      return;
    }
    this.liberarScrollPagina();
  }

  private bloquearScrollPagina(): void {
    if (this.overflowBodyAnterior !== null) return;
    this.overflowBodyAnterior = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
  }

  private liberarScrollPagina(): void {
    if (this.overflowBodyAnterior === null) return;
    document.body.style.overflow = this.overflowBodyAnterior;
    this.overflowBodyAnterior = null;
  }

  private carregar(loteId: number): void {
    this.carregando = true;
    this.estoqueService.rastreabilidadeLote(loteId).subscribe({
      next: rastreabilidade => {
        if (this.loteId === loteId) this.rastreabilidade = rastreabilidade;
        if (this.loteId === loteId) this.carregando = false;
      },
      error: () => {
        if (this.loteId === loteId) {
          this.erro = 'Não foi possível carregar a rastreabilidade do lote.';
          this.carregando = false;
        }
      },
    });
  }
}
