import { FiltroConfig } from './../../model/filtro-config';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { OrdemEntregaService } from '../../service/ordem-entrega.service';
import { OrdemEntrega } from '../../model/ordem_entrega';
import { ItemOrdemService } from '../../service/item-ordem.service';
import { ItemOrdem } from '../../model/itemOrdem';
import { ItemOrdemInsert } from '../../model/itemOrdem_insert';
import { FormsModule } from '@angular/forms';
import { forkJoin, Observable, of, switchMap } from 'rxjs';
import { EmpenhoService } from '../../service/empenho.service';
import { Empenho } from '../../model/empenho';
import { ItemEmpenhoService } from '../../service/item-empenho.service';
import { Paginacao } from '../utils/paginacao/paginacao';
import { FeedbackService } from '../../service/feedback.service';
import { EstadoConteudo } from '../utils/estado-conteudo/estado-conteudo';
import { Acao, pode, Recurso } from '../../security/rbac';
import { EstadoListagemService } from '../../service/estado-listagem.service';

@Component({
  selector: 'app-visualizar-entregas',
  standalone: true,
  imports: [BarraPesquisa, CommonModule, FormsModule, Paginacao, RouterLink, EstadoConteudo],
  templateUrl: './visualizar-entregas.html',
  styleUrl: './visualizar-entregas.scss',
})
export class VisualizarEntregas {
  readonly pode = pode;
  readonly Acao = Acao;
  readonly Recurso = Recurso;

  filtros: FiltroConfig[] = [
  {
    campo: 'status',
    label: 'Status da entrega',
    tipo: 'radio',
    opcoes: [
      { valor: 'esp', label: 'Entrega em espera' },
      { valor: 'par', label: 'Entrega parcial' },
      { valor: 'con', label: 'Entrega realizada' }
    ]
  },
  {
    campo: 'data_emissao',
    label: 'Data de emissão',
    tipo: 'date-range'
  },
  {
    campo: 'data_entrega_prevista',
    label: 'Previsão de entrega',
    tipo: 'date-range'
  }
];

  filtrosAtivos: any = {};
  empenhoContextoId: number | null = null;
  empenhoContexto: Empenho | null = null;

  confirmado: boolean = false;
  isLoadingEntregas: boolean = false;
  isLoadingPedidos: boolean = false;
  isConfirmandoEntrega: boolean = false;
  etapaConfirmacao: 1 | 2 = 1;
  formSubmittedConfirmacao: boolean = false;
  errorMessagePage: string = '';
  errorMessageModal: string = '';
  currentPage: number = 1;
  pageSize: number = 3;
  total: number = 0;
  hasNext: boolean = false;
  hasPrev: boolean = false;
  termoBuscaAtual: string = '';
  private permitirFecharModalSemConfirmacao: boolean = false;
  private estadoInicialPedidosModal: Array<{ id: number; quantidade_entregue: number; observacao: string }> = [];

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private ordemEntregaService: OrdemEntregaService,
    private itensOrdemService: ItemOrdemService,
    private empenhoService: EmpenhoService,
    private itemEmpenhoService: ItemEmpenhoService,
    private feedback: FeedbackService,
    private estadoListagem: EstadoListagemService
  ) { }

  entregas: OrdemEntrega[] = [];
  pedidosDaOrdem: ItemOrdem[] = [];
  ordemSelecionada: number = 0;

  @ViewChild('confirmarModalRef') modal!: ElementRef;
  @ViewChild('myInput') input?: ElementRef;
  @ViewChild('fecharConfirmacaoInternoBtn') fecharConfirmacaoInternoBtn!: ElementRef<HTMLButtonElement>;

  get possuiEntregaParcialSemObservacao(): boolean {
    return this.pedidosDaOrdem.some((item) => this.precisaObservacao(item) && !this.observacaoPreenchida(item));
  }

  get possuiQuantidadeInvalida(): boolean {
    return this.pedidosDaOrdem.some((item) => !this.quantidadeEntregueValida(item));
  }

  get possuiQuantidadeEntregueInformada(): boolean {
    return this.pedidosDaOrdem.some((item) => Number(item.quantidade_entregue) > 0);
  }

  get podeConfirmarEntrega(): boolean {
    if (this.isConfirmandoEntrega || this.isLoadingPedidos || this.pedidosDaOrdem.length === 0) {
      return false;
    }

    return !this.possuiQuantidadeInvalida && !this.possuiEntregaParcialSemObservacao && this.possuiQuantidadeEntregueInformada;
  }

  get ordemSelecionadaAtual(): OrdemEntrega | null {
    return this.entregas[this.ordemSelecionada] || null;
  }

  get valorSolicitadoConfirmacao(): number {
    return this.pedidosDaOrdem.reduce((acumulador, item) => {
      const quantidadeSolicitada = Number(item.quantidade_solicitada) || 0;
      const valorUnitario = Number(item.item_empenho?.item_ata?.valor_unitario) || 0;
      const valorItem = Number((quantidadeSolicitada * valorUnitario).toFixed(2));

      return Number((acumulador + valorItem).toFixed(2));
    }, 0);
  }

  get valorRecebidoConfirmacao(): number {
    return this.calcularSomaValorEntregue(this.pedidosDaOrdem);
  }

  get valorPendenteConfirmacao(): number {
    return Number(Math.max(this.valorSolicitadoConfirmacao - this.valorRecebidoConfirmacao, 0).toFixed(2));
  }

  get itensRecebidosIntegralmente(): number {
    return this.pedidosDaOrdem.filter((item) =>
      Number(item.quantidade_entregue) === Number(item.quantidade_solicitada)
    ).length;
  }

  get itensRecebidosParcialmente(): number {
    return this.pedidosDaOrdem.filter((item) => {
      const quantidadeEntregue = Number(item.quantidade_entregue);
      const quantidadeSolicitada = Number(item.quantidade_solicitada);

      return quantidadeEntregue > 0 && quantidadeEntregue < quantidadeSolicitada;
    }).length;
  }

  get itensSemRecebimento(): number {
    return this.pedidosDaOrdem.filter((item) => Number(item.quantidade_entregue) === 0).length;
  }

  get possuiDadosModalPreenchidos(): boolean {
    if (!this.pedidosDaOrdem.length || !this.estadoInicialPedidosModal.length) {
      return false;
    }

    return this.pedidosDaOrdem.some((item) => {
      const estadoInicial = this.estadoInicialPedidosModal.find((registro) => registro.id === item.id);
      if (!estadoInicial) {
        return false;
      }

      const quantidadeAtual = Number(item.quantidade_entregue) || 0;
      const observacaoAtual = (item.observacao || '').trim();

      return quantidadeAtual !== estadoInicial.quantidade_entregue || observacaoAtual !== estadoInicial.observacao;
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

  ngOnInit() {
    const empenhoId = Number(this.route.snapshot.queryParamMap.get('empenho_id'));

    if (Number.isInteger(empenhoId) && empenhoId > 0) {
      this.empenhoContextoId = empenhoId;

      this.restaurarEstadoListagem();
      this.filtrosAtivos = {
        ...this.filtrosAtivos,
        'empenho__id': empenhoId
      };

      this.empenhoService.getById(empenhoId).subscribe({
        next: (empenho) => {
          this.empenhoContexto = empenho;
        },
        error: () => {
          this.empenhoContexto = null;
        }
      });
    } else {
      this.restaurarEstadoListagem();
    }

    this.getEntregas();
  }

  ngAfterViewInit() {
    const modalElement = this.modal?.nativeElement;
    if (!modalElement) {
      return;
    }

    modalElement.addEventListener('shown.bs.modal', () => {
      if (this.input?.nativeElement) {
        this.input.nativeElement.focus();
      }
    });

    modalElement.addEventListener('hide.bs.modal', (event: Event) => {
      if (this.permitirFecharModalSemConfirmacao) {
        this.permitirFecharModalSemConfirmacao = false;
        return;
      }

      if (this.isConfirmandoEntrega) {
        event.preventDefault();
        return;
      }

      if (this.possuiDadosModalPreenchidos) {
        event.preventDefault();
        this.confirmarDescarteModalConfirmacao();
      }
    });

  }

  getEntregas(termobusca?: string) {
    if (termobusca !== undefined) {
      this.termoBuscaAtual = termobusca;
      this.currentPage = 1;
      this.salvarEstadoListagem();
    }

    this.isLoadingEntregas = true;
    this.errorMessagePage = '';

    this.ordemEntregaService.get(this.termoBuscaAtual, this.currentPage, this.pageSize, this.filtrosAtivos).subscribe({
      next: (resposta) => {
        this.entregas = this.ordenarEntregaPorStatusEData(resposta.results);
        this.total = resposta.count;
        this.hasNext = Boolean(resposta.next);
        this.hasPrev = Boolean(resposta.previous);
        this.isLoadingEntregas = false;
      },
      error: () => {
        this.isLoadingEntregas = false;
        this.errorMessagePage = 'Não foi possível carregar as entregas no momento.';
      }
    });

  }

  proximaPagina(): void {
    if (!this.hasNext) {
      return;
    }

    this.currentPage += 1;
    this.salvarEstadoListagem();
    this.getEntregas();
  }

  paginaAnterior(): void {
    if (!this.hasPrev || this.currentPage === 1) {
      return;
    }

    this.currentPage -= 1;
    this.salvarEstadoListagem();
    this.getEntregas();
  }

  irParaPagina(page: number): void {
    if (page === this.currentPage) {
      return;
    }

    this.currentPage = page;
    this.salvarEstadoListagem();
    this.getEntregas();
  }

  getItensOrdem(id: number, index: number) {
    this.ordemSelecionada = index;
    this.etapaConfirmacao = 1;
    this.formSubmittedConfirmacao = false;
    this.errorMessageModal = '';
    this.isLoadingPedidos = true;

    this.ordemEntregaService.getPedidos(id).subscribe({
      next: (registro: ItemOrdem[]) => {
        this.pedidosDaOrdem = registro;
        this.estadoInicialPedidosModal = registro.map((item) => ({
          id: item.id,
          quantidade_entregue: Number(item.quantidade_entregue) || 0,
          observacao: (item.observacao || '').trim()
        }));
      },
      error: () => {
        this.errorMessageModal = 'Não foi possível carregar os itens desta entrega.';
      },
      complete: () => {
        this.isLoadingPedidos = false;
      }
    });

  }

  verificarStatus(status: string): string {
    if (status === "esp") {
      return "Entrega em espera";
    }
    if (status === "par") {
      return "Entrega parcial";
    }
    return "Entrega realizada";
  }

  classeStatus(status: string): string {
    if (status === "esp") {
      return "em_espera";
    }
    if (status === "par") {
      return "parcial";
    }
    return "realizada";
  }

  ordenarEntregaPorStatusEData(entregas: OrdemEntrega[]): OrdemEntrega[] {
    return entregas.sort((a, b) => {
      if (a.status === b.status) {
        return new Date(a.data_emissao).getTime() - new Date(b.data_emissao).getTime();
      }
      const prioridade: Record<string, number> = { par: 0, esp: 1, con: 2 };
      return (prioridade[a.status] ?? 3) - (prioridade[b.status] ?? 3);
    });
  }

  verificarQuantidadeEntregue(item: ItemOrdem) {
    if (item.quantidade_entregue === null || item.quantidade_entregue === undefined || Number.isNaN(Number(item.quantidade_entregue))) {
      item.quantidade_entregue = 0;
    }

    if (item.quantidade_entregue > item.quantidade_solicitada) {
      item.quantidade_entregue = item.quantidade_solicitada;
    }

    if (item.quantidade_entregue < 0) {
      item.quantidade_entregue = 0;
    }
  }

  quantidadeEntregueValida(item: ItemOrdem): boolean {
    const quantidadeEntregue = Number(item.quantidade_entregue);
    const quantidadeSolicitada = Number(item.quantidade_solicitada);

    return Number.isFinite(quantidadeEntregue) && quantidadeEntregue >= 0 && quantidadeEntregue <= quantidadeSolicitada;
  }

  observacaoValida(item: ItemOrdem): boolean {
    const observacao = (item.observacao || '').trim();

    if (observacao.length > 300) {
      return false;
    }

    if (this.precisaObservacao(item)) {
      return observacao.length > 0;
    }

    return true;
  }

  itemEntregaValido(item: ItemOrdem): boolean {
    return this.quantidadeEntregueValida(item) && this.observacaoValida(item);
  }

  marcarTodosComoRecebidos(): void {
    if (this.isConfirmandoEntrega) {
      return;
    }

    this.pedidosDaOrdem.forEach((item) => {
      item.quantidade_entregue = Number(item.quantidade_solicitada) || 0;
    });
  }

  irParaRevisaoConfirmacao(): void {
    this.formSubmittedConfirmacao = true;
    this.errorMessageModal = '';

    if (!this.podeConfirmarEntrega) {
      this.errorMessageModal = 'Revise as quantidades e observações antes de continuar.';
      return;
    }

    this.etapaConfirmacao = 2;
  }

  voltarParaRegistroConfirmacao(): void {
    if (this.isConfirmandoEntrega) {
      return;
    }

    this.etapaConfirmacao = 1;
  }

  classeRecebimentoItem(item: ItemOrdem): 'integral' | 'parcial' | 'pendente' {
    const quantidadeEntregue = Number(item.quantidade_entregue) || 0;
    const quantidadeSolicitada = Number(item.quantidade_solicitada) || 0;

    if (quantidadeEntregue === quantidadeSolicitada) {
      return 'integral';
    }

    return quantidadeEntregue > 0 ? 'parcial' : 'pendente';
  }

  textoRecebimentoItem(item: ItemOrdem): string {
    const estado = this.classeRecebimentoItem(item);

    if (estado === 'integral') {
      return 'Recebido integralmente';
    }

    if (estado === 'parcial') {
      return 'Recebimento parcial';
    }

    return 'Não recebido';
  }

  calcularValorRecebidoItem(item: ItemOrdem): number {
    const valorUnitario = Number(item.item_empenho?.item_ata?.valor_unitario) || 0;
    const quantidadeEntregue = Number(item.quantidade_entregue) || 0;

    return Number((valorUnitario * quantidadeEntregue).toFixed(2));
  }

  calcularValorPendenteItem(item: ItemOrdem): number {
    const valorUnitario = Number(item.item_empenho?.item_ata?.valor_unitario) || 0;
    const quantidadePendente = Math.max(
      (Number(item.quantidade_solicitada) || 0) - (Number(item.quantidade_entregue) || 0),
      0
    );

    return Number((valorUnitario * quantidadePendente).toFixed(2));
  }

  calcularQuantidadePendenteItem(item: ItemOrdem): number {
    return Math.max(
      (Number(item.quantidade_solicitada) || 0) -
      (Number(item.quantidade_entregue) || 0),
      0
    );
  }

  tentarFecharModalConfirmacao(): void {
    if (this.isConfirmandoEntrega) {
      return;
    }

    if (this.possuiDadosModalPreenchidos) {
      this.confirmarDescarteModalConfirmacao();
      return;
    }

    this.fecharModalConfirmacaoSemConfirmacao();
  }

  private confirmarDescarteModalConfirmacao(): void {
    this.feedback.confirmar({
      titulo: 'Descartar alterações?',
      mensagem: 'Você já preencheu dados da confirmação de entrega. Se sair agora, perderá toda a operação. Deseja sair mesmo assim?',
      textoConfirmar: 'Descartar',
      textoCancelar: 'Continuar editando',
      destrutiva: true
    }).then((desejaSair) => {
      if (desejaSair) {
        this.fecharModalConfirmacaoSemConfirmacao();
      }
    });
  }

  private fecharModalConfirmacaoSemConfirmacao(): void {
    if (this.fecharConfirmacaoInternoBtn?.nativeElement) {
      this.permitirFecharModalSemConfirmacao = true;
      this.fecharConfirmacaoInternoBtn.nativeElement.click();
    }
  }

  private precisaObservacao(item: ItemOrdem): boolean {
    return Number(item.quantidade_entregue) < Number(item.quantidade_solicitada);
  }

  private observacaoPreenchida(item: ItemOrdem): boolean {
    return Boolean((item.observacao || '').trim());
  }

  confirmarEntrega(ordemIndex: number): void {
    this.formSubmittedConfirmacao = true;

    if (!this.podeConfirmarEntrega) {
      this.errorMessageModal = 'Revise os campos obrigatórios antes de confirmar a entrega.';
      return;
    }

    this.errorMessageModal = '';
    this.isConfirmandoEntrega = true;

    const ordem = this.entregas[ordemIndex];
    const somaValorEntregue = this.calcularSomaValorEntregue(this.pedidosDaOrdem);

    this.atualizarItensDaOrdem(this.pedidosDaOrdem).pipe(
      switchMap(() => this.atualizarOrdemComoConcluida(ordem.id)),
      switchMap(() => this.atualizarSaldoEmpenho(ordem.empenho.id, ordem.empenho.saldo_utilizado, somaValorEntregue))
    ).subscribe({
      complete: () => {
        this.isConfirmandoEntrega = false;
        this.fecharModalConfirmacaoSemConfirmacao();
        this.feedback.sucesso('Entrega confirmada com sucesso.');
        this.getEntregas();
      },
      error: (err) => {
        console.error('Erro ao confirmar entrega', err);
        this.errorMessageModal = 'Não foi possível confirmar a entrega. Tente novamente.';
        this.isConfirmandoEntrega = false;
      }
    });
  }

  private calcularSomaValorEntregue(itens: ItemOrdem[]): number {
    return itens.reduce((acc, item) => {
      const valorItem = Number(
        (Number(item.item_empenho.item_ata.valor_unitario) * Number(item.quantidade_entregue)).toFixed(2)
      );
      return Number((acc + valorItem).toFixed(2));
    }, 0);
  }

  private atualizarItensDaOrdem(itens: ItemOrdem[]): Observable<any> {
    if (!itens.length) return of(null);

    const requests = itens.map(item => {
      const itemUpdate = {
        quantidade_entregue: item.quantidade_entregue,
        observacao: item.observacao
      };

      const itemEmpenhoUpdate = {
        quantidade_entrege: item.quantidade_entregue
      };

      return this.itensOrdemService.patch(item.id, itemUpdate).pipe(
        switchMap(() =>
          this.itemEmpenhoService.patch(item.item_empenho.id, itemEmpenhoUpdate)
        )
      );
    });

    return forkJoin(requests);
  }

  private atualizarOrdemComoConcluida(ordemId: number): Observable<any> {
    const ordemUpdate = {
      status: 'con',
      data_entrega: new Date()
    };
    return this.ordemEntregaService.patch(ordemId, ordemUpdate);
  }

  private atualizarSaldoEmpenho(empenhoId: number, saldoAtual: number, somaValorEntregue: number): Observable<any> {
    const novoSaldo = Number((Number(saldoAtual) + somaValorEntregue).toFixed(2));
    return this.empenhoService.patch(empenhoId, { saldo_utilizado: novoSaldo });
  }

  aplicarFiltros(filtros: any) {
    this.filtrosAtivos = {
      ...filtros,
      ...(this.empenhoContextoId
        ? { 'empenho__id': this.empenhoContextoId }
        : {})
    };
    this.currentPage = 1;
    this.salvarEstadoListagem();
    this.getEntregas();
  }

  private get chaveEstadoListagem(): string {
    return this.empenhoContextoId
      ? `entregas-empenho-${this.empenhoContextoId}`
      : 'entregas';
  }

  salvarEstadoListagem(): void {
    const filtrosVisuais = { ...this.filtrosAtivos };
    delete filtrosVisuais['empenho__id'];

    this.estadoListagem.salvar(this.chaveEstadoListagem, {
      termoBuscaAtual: this.termoBuscaAtual,
      filtrosAtivos: filtrosVisuais,
      currentPage: this.currentPage
    });
  }

  private restaurarEstadoListagem(): void {
    const estado = this.estadoListagem.obter(this.chaveEstadoListagem);
    if (!estado) {
      return;
    }

    this.termoBuscaAtual = estado.termoBuscaAtual;
    this.filtrosAtivos = { ...estado.filtrosAtivos };
    this.currentPage = estado.currentPage;
  }

  limparContextoEmpenho(): void {
    this.empenhoContextoId = null;
    this.empenhoContexto = null;

    const filtrosSemContexto = { ...this.filtrosAtivos };
    delete filtrosSemContexto['empenho__id'];
    this.filtrosAtivos = filtrosSemContexto;
    this.currentPage = 1;
    this.salvarEstadoListagem();

    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { empenho_id: null },
      queryParamsHandling: 'merge'
    });

    this.getEntregas();
  }
}
