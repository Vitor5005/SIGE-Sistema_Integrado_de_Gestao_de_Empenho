import { CommonModule } from '@angular/common';
import { Component, EventEmitter, HostListener, Input, OnChanges, OnDestroy, Output, SimpleChanges } from '@angular/core';

import { EstoqueItem, LoteValidade, StatusValidade } from '../../../model/estoque';
import { Acao, pode, Recurso } from '../../../security/rbac';
import { EstoqueService } from '../../../service/estoque.service';
import { Paginacao } from '../../utils/paginacao/paginacao';
import { RastreabilidadeLote } from '../rastreabilidade-lote/rastreabilidade-lote';

@Component({
  selector: 'app-detalhes-lotes-estoque',
  standalone: true,
  imports: [CommonModule, Paginacao, RastreabilidadeLote],
  templateUrl: './detalhes-lotes-estoque.html',
  styleUrl: '../estoque.scss',
})
export class DetalhesLotesEstoque implements OnChanges, OnDestroy {
  @Input() item: EstoqueItem | null = null;
  @Output() fechar = new EventEmitter<void>();

  readonly pode = pode;
  readonly Recurso = Recurso;
  readonly Acao = Acao;

  lotes: LoteValidade[] = [];
  currentPage = 1;
  pageSize = 10;
  total = 0;
  carregando = false;
  erro = '';
  loteSelecionadoId: number | null = null;
  private overflowBodyAnterior: string | null = null;

  constructor(private estoqueService: EstoqueService) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['item']) {
      return;
    }

    this.loteSelecionadoId = null;
    this.erro = '';
    this.lotes = [];
    this.currentPage = 1;
    this.total = 0;
    this.carregando = false;

    if (this.item) {
      this.bloquearScrollPagina();
      this.carregarLotes();
    } else {
      this.liberarScrollPagina();
    }
  }

  ngOnDestroy(): void {
    this.liberarScrollPagina();
  }

  get podeConsultarHistorico(): boolean {
    return this.pode(this.Recurso.MOVIMENTACAO_ESTOQUE, this.Acao.CONSULTAR_EXTRATO);
  }

  get podeVerValidadeEstoquista(): boolean {
    return this.pode(this.Recurso.ESTOQUE, this.Acao.REGISTRAR_SAIDA);
  }

  get podeVerValidadeNutricionista(): boolean {
    return this.pode(this.Recurso.PAINEL_NUTRICIONISTA, this.Acao.CONSULTAR);
  }

  get podeVerIndicadoresValidade(): boolean {
    return this.podeVerValidadeEstoquista || this.podeVerValidadeNutricionista;
  }

  get deveExibirResumoValidade(): boolean {
    const item = this.item;

    return item !== null
      && this.podeVerIndicadoresValidade
      && (this.temValidadePrioritaria(item) || item.proxima_validade !== null);
  }

  get rotuloProximaValidade(): string {
    return this.podeVerValidadeEstoquista ? 'Próxima validade utilizável' : 'Próxima validade';
  }

  get loteSelecionado(): LoteValidade | undefined {
    return this.lotes.find(lote => lote.id === this.loteSelecionadoId);
  }

  @HostListener('document:keydown.escape')
  aoPressionarEscape(): void {
    if (this.item !== null) {
      this.fecharModal();
    }
  }

  carregarLotes(): void {
    if (!this.item) {
      return;
    }

    const itemGenericoId = this.item.item_generico_id;
    this.carregando = true;
    this.erro = '';
    this.estoqueService.listarLotesValidade('', this.currentPage, this.pageSize, {
      item_generico_id: itemGenericoId,
      saldo_positivo: false,
    }).subscribe({
      next: resposta => {
        if (this.item?.item_generico_id !== itemGenericoId) {
          return;
        }

        this.lotes = resposta.results;
        this.total = resposta.count;
        this.carregando = false;
      },
      error: () => {
        if (this.item?.item_generico_id !== itemGenericoId) {
          return;
        }

        this.lotes = [];
        this.total = 0;
        this.erro = 'Não foi possível carregar os lotes deste gênero.';
        this.carregando = false;
      },
    });
  }

  irParaPagina(page: number): void {
    this.currentPage = page;
    this.carregarLotes();
  }

  alterarPageSize(pageSize: number): void {
    this.pageSize = pageSize;
    this.currentPage = 1;
    this.carregarLotes();
  }

  selecionarLote(lote: LoteValidade): void {
    if (this.podeConsultarHistorico) {
      this.loteSelecionadoId = lote.id;
    }
  }

  selecionarLotePorTeclado(event: KeyboardEvent, lote: LoteValidade): void {
    if (event.key !== 'Enter' && event.key !== ' ') {
      return;
    }

    event.preventDefault();
    this.selecionarLote(lote);
  }

  voltarAosLotes(): void {
    this.loteSelecionadoId = null;
  }

  fecharModal(): void {
    this.fechar.emit();
  }

  private bloquearScrollPagina(): void {
    if (this.overflowBodyAnterior !== null) {
      return;
    }

    this.overflowBodyAnterior = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
  }

  private liberarScrollPagina(): void {
    if (this.overflowBodyAnterior === null) {
      return;
    }

    document.body.style.overflow = this.overflowBodyAnterior;
    this.overflowBodyAnterior = null;
  }

  temValidadePrioritaria(item: EstoqueItem): boolean {
    return (this.podeVerValidadeEstoquista && item.lotes_vencidos > 0)
      || item.lotes_vence_hoje > 0
      || item.lotes_criticos > 0
      || item.lotes_atencao > 0;
  }

  textoProximaValidade(item: EstoqueItem): string {
    if (!item.proxima_validade || item.dias_para_proxima_validade === null) {
      return '';
    }

    const dias = item.dias_para_proxima_validade;
    const prazo = dias === 0 ? 'hoje' : `${dias} ${dias === 1 ? 'dia' : 'dias'}`;

    return `${this.formatarDataCivil(item.proxima_validade)} · ${prazo}`;
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
        return 'text-success';
      default:
        return 'text-body-secondary';
    }
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
