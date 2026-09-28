import { Component, ElementRef, ViewChild } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { BotaoVoltar } from '../utils/botao-voltar/botao-voltar';
import { CommonModule } from '@angular/common';
import { EmpenhoService } from '../../service/empenho.service';
import { Empenho } from '../../model/empenho';
import { ItemEmpenho } from '../../model/itemEmpenho';
import { OperacaoItem } from '../../model/operacao_item';
import { OperacaoItemService } from '../../service/operacao-item.service';
import { OperacaoItemInsert } from '../../model/operacao_item_insert';
import { FormsModule } from '@angular/forms';
import { ItemEmpenhoService } from '../../service/item-empenho.service';
import { ItemOrdemInsert } from '../../model/itemOrdem_insert';
import { OrdemEntregaInsert } from '../../model/ordem_entrega_insert';
import { ItemOrdemService } from '../../service/item-ordem.service';
import { OrdemEntregaService } from '../../service/ordem-entrega.service';
import { forkJoin, switchMap } from 'rxjs';
import { ItemOrdem } from '../../model/itemOrdem';
import { FeedbackService } from '../../service/feedback.service';
import { EstadoConteudo } from '../utils/estado-conteudo/estado-conteudo';
import { Acao, pode, Recurso } from '../../security/rbac';
import { SolicitacaoReforco, StatusSolicitacaoReforco } from '../../model/solicitacao_reforco';
import { SolicitacaoReforcoService } from '../../service/solicitacao-reforco.service';

@Component({
  selector: 'app-visualizar-empenho',
  imports: [BotaoVoltar, CommonModule, FormsModule, RouterLink, EstadoConteudo],
  templateUrl: './visualizar-empenho.html',
  styleUrl: './visualizar-empenho.scss',
})
export class VisualizarEmpenho {
  readonly pode = pode;
  readonly Acao = Acao;
  readonly Recurso = Recurso;
  tipo: 'reforco' | 'anulacao' = 'reforco';
  isSolicitandoEntrega: boolean = false;
  etapaSolicitacao: 1 | 2 | 3 = 1;
  isLoadingPage: boolean = true;
  errorMessagePage: string = '';
  idPagina: number | null = null;
  isLoadingItens: boolean = false;
  errorMessageItens: string = '';
  isLoadingOperacoes: boolean = false;
  errorMessageOperacoes: string = '';
  empenhoEdicao = {
    codigo: ''
  };
  formSubmittedEdicaoEmpenho: boolean = false;
  isSavingEdicaoEmpenho: boolean = false;
  errorMessageEdicaoEmpenho: string = '';
  private permitirFecharModalSemConfirmacao: boolean = false;
  constructor(
    private router: Router,
    private empenhoService: EmpenhoService,
    private operacaoItemService: OperacaoItemService,
    private itemEmpenhoService: ItemEmpenhoService,
    private ordemEntregaService: OrdemEntregaService,
    private itemOrdemService: ItemOrdemService,
    private route: ActivatedRoute,
    private solicitacaoReforcoService: SolicitacaoReforcoService,
    private feedback: FeedbackService
  ) { }

  @ViewChild('fecharSolicitacaoReforcoBtn') fecharSolicitacaoReforcoBtn?: ElementRef<HTMLButtonElement>;

  solicitacoesReforco: SolicitacaoReforco[] = [];
  itemReforco: ItemEmpenho | null = null;
  saldoReforco: number | null = null;
  quantidadeReforco: number | null = null;
  justificativaReforco = '';
  enviandoReforco = false;
  erroSolicitacaoReforco = '';
  respondendoReforcoId: number | null = null;
  recusandoReforcoId: number | null = null;
  motivoRecusaReforco = '';
  erroRespostaReforco = '';

  get podeEnviarSolicitacaoReforco(): boolean {
    const quantidade = Number(this.quantidadeReforco);
    return !this.enviandoReforco
      && this.saldoReforco !== null
      && quantidade >= 1
      && quantidade <= this.saldoReforco
      && this.justificativaReforco.trim().length > 0;
  }

  textoStatusReforco(status: StatusSolicitacaoReforco): string {
    return { PENDENTE: 'Aguardando Diretor', ATENDIDA: 'Atendida', RECUSADA: 'Recusada' }[status];
  }

  getSolicitacoesReforco(empenhoId: number): void {
    if (!pode(Recurso.SOLICITACAO_REFORCO, Acao.CONSULTAR)) {
      return;
    }
    this.solicitacaoReforcoService.listar({ empenhoId }).subscribe({
      next: (resposta) => this.solicitacoesReforco = resposta.results,
    });
  }

  abrirSolicitacaoReforco(item: ItemEmpenho): void {
    this.itemReforco = item;
    this.saldoReforco = null;
    this.quantidadeReforco = null;
    this.justificativaReforco = '';
    this.erroSolicitacaoReforco = '';
    this.solicitacaoReforcoService.saldoDisponivel(item.id).subscribe({
      next: (saldo) => this.saldoReforco = saldo,
      error: () => this.erroSolicitacaoReforco = 'Não foi possível consultar o saldo da ARP.',
    });
  }

  enviarSolicitacaoReforco(): void {
    if (!this.itemReforco || !this.podeEnviarSolicitacaoReforco) {
      return;
    }
    this.enviandoReforco = true;
    this.erroSolicitacaoReforco = '';
    this.solicitacaoReforcoService
      .solicitar(this.itemReforco.id, Number(this.quantidadeReforco), this.justificativaReforco.trim())
      .subscribe({
        next: () => {
          this.enviandoReforco = false;
          this.fecharSolicitacaoReforcoBtn?.nativeElement.click();
          this.feedback.sucesso('Solicitação de reforço enviada ao Diretor.');
          this.getSolicitacoesReforco(this.empenho.id);
        },
        error: (erro) => {
          this.enviandoReforco = false;
          this.erroSolicitacaoReforco = this.mensagemErroApi(erro, 'Não foi possível enviar a solicitação.');
        },
      });
  }

  atenderReforco(solicitacao: SolicitacaoReforco): void {
    this.responderReforco(solicitacao, this.solicitacaoReforcoService.atender(solicitacao.id), true);
  }

  recusarReforco(solicitacao: SolicitacaoReforco): void {
    this.responderReforco(
      solicitacao,
      this.solicitacaoReforcoService.recusar(solicitacao.id, this.motivoRecusaReforco.trim()),
      false,
    );
  }

  private responderReforco(solicitacao: SolicitacaoReforco, requisicao: ReturnType<SolicitacaoReforcoService['atender']>, alterouSaldos: boolean): void {
    this.respondendoReforcoId = solicitacao.id;
    this.erroRespostaReforco = '';
    requisicao.subscribe({
      next: () => {
        this.respondendoReforcoId = null;
        this.recusandoReforcoId = null;
        this.getSolicitacoesReforco(this.empenho.id);
        if (alterouSaldos) {
          this.getEmpenho(this.empenho.id);
          this.getItensEmpenho(this.empenho.id);
          this.getOperacoesEmpenho(this.empenho.id);
        }
      },
      error: (erro) => {
        this.respondendoReforcoId = null;
        this.erroRespostaReforco = this.mensagemErroApi(erro, 'Não foi possível responder a solicitação.');
      },
    });
  }

  private mensagemErroApi(erro: any, padrao: string): string {
    const valor = erro?.error && typeof erro.error === 'object' ? Object.values(erro.error)[0] : null;
    return Array.isArray(valor) ? String(valor[0]) : (typeof valor === 'string' ? valor : padrao);
  }

  empenho: Empenho = <Empenho>{};
  itensEmpenho: ItemEmpenho[] = [];
  itemEmpenhoModal: ItemEmpenho = <ItemEmpenho>{};
  itensOrdemInsert: ItemOrdemInsert[] = [];
  ordemEntregaInsert: OrdemEntregaInsert = <OrdemEntregaInsert>{};
  itensSelecionados: boolean[] = [];
  mensagemSolicitacao: string = '';
  arquivoSolicitacao: File | null = null;

  get possuiItensSelecionados(): boolean {
    return this.itensSelecionados.some(Boolean);
  }

  get todosItensDisponiveisSelecionados(): boolean {
    const itensDisponiveis = this.itensEmpenho
      .map((item, index) => ({ item, index }))
      .filter(({ item }) => Number(item.quantidade_atual) > 0);

    return itensDisponiveis.length > 0 && itensDisponiveis.every(({ index }) => this.itensSelecionados[index]);
  }

  get saldoNaoUtilizado(): number {
    const valorEmpenhado = Number(this.empenho?.valor_total || 0);
    const valorUtilizado = Number(this.empenho?.saldo_utilizado || 0);

    return Math.max(valorEmpenhado - valorUtilizado, 0);
  }

  get percentualUtilizado(): number {
    const valorEmpenhado = Number(this.empenho?.valor_total || 0);
    const valorUtilizado = Number(this.empenho?.saldo_utilizado || 0);

    if (valorEmpenhado <= 0) {
      return 0;
    }

    return Math.min(100, Math.max(0, (valorUtilizado / valorEmpenhado) * 100));
  }

  get placeholderMensagemSolicitacao(): string {
    const fornecedor = this.empenho?.ata?.fornecedor?.nome_fantasia || '[Fornecedor]';
    return (
      `Prezado Fornecedor ${fornecedor},\n\n` +
      `Segue em anexo o pedido de entrega referente à ordem ${this.empenho?.ata?.numero_ata || '[Código]'}.\n\n` +
      `Atenciosamente,\nEquipe SIGE.`
    );
  }

  get dataPrevisaoPreenchida(): boolean {
    const dataSelecionada = this.ordemEntregaInsert?.data_entrega_prevista;
    if (!dataSelecionada) {
      return false;
    }

    const hoje = new Date(this.todayDate + 'T00:00:00');
    const dataInformada = new Date(dataSelecionada + 'T00:00:00');
    return dataInformada >= hoje;
  }

  get arquivoPreenchido(): boolean {
    return this.arquivoSolicitacao instanceof File;
  }

  get fornecedorPodeReceberPedido(): boolean {
    return Boolean(this.empenho?.ata?.fornecedor?.email?.trim());
  }

  get nomeArquivoSolicitacao(): string {
    return this.arquivoSolicitacao?.name || 'Nenhum arquivo selecionado';
  }

  get podeAvancarDadosSolicitacao(): boolean {
    return (
      !this.isSolicitandoEntrega &&
      this.dataPrevisaoPreenchida &&
      this.arquivoPreenchido &&
      this.fornecedorPodeReceberPedido
    );
  }

  get itensSelecionadosCount(): number {
    return this.itensSelecionados.filter(Boolean).length;
  }

  get itensSelecionadosComQuantidadeValida(): boolean {
    if (!this.possuiItensSelecionados) {
      return false;
    }

    return this.itensEmpenho.every((item, index) => {
      if (!this.itensSelecionados[index]) {
        return true;
      }

      return this.ehQuantidadeSolicitadaValida(index, item);
    });
  }

  get podeAvancarItensSolicitacao(): boolean {
    return (
      !this.isSolicitandoEntrega &&
      this.possuiItensSelecionados &&
      this.itensSelecionadosComQuantidadeValida
    );
  }

  get podeSolicitarEntrega(): boolean {
    return (
      !this.isSolicitandoEntrega &&
      this.possuiItensSelecionados &&
      this.dataPrevisaoPreenchida &&
      this.arquivoPreenchido &&
      this.fornecedorPodeReceberPedido &&
      this.itensSelecionadosComQuantidadeValida
    );
  }

  get todayDate(): string {
    const hoje = new Date();
    const ano = hoje.getFullYear();
    const mes = String(hoje.getMonth() + 1).padStart(2, '0');
    const dia = String(hoje.getDate()).padStart(2, '0');

    return `${ano}-${mes}-${dia}`;
  }

  get possuiDadosPreenchidosModal(): boolean {
    const possuiData = Boolean(this.ordemEntregaInsert?.data_entrega_prevista);
    const possuiMensagem = Boolean(this.mensagemSolicitacao?.trim());
    const possuiArquivo = this.arquivoPreenchido;

    const possuiQuantidadePreenchida = this.itensEmpenho.some((item, index) => {
      if (!this.itensSelecionados[index]) {
        return false;
      }
      const quantidade = Number(this.itensOrdemInsert[index]?.quantidade_solicitada) || 0;
      return quantidade > 0;
    });

    return possuiData || possuiMensagem || possuiArquivo || possuiQuantidadePreenchida;
  }

  operacoesEmpenho: OperacaoItem[] = [];
  operacaoItem_insercao: OperacaoItemInsert = <OperacaoItemInsert>{ data: new Date(), tipo: 'inc', item_empenho: 0, valor: 0 };

  categoria = {
    "tempS": "Tempero Secos",
    "SM": "Secos / Mercearia",
    "Lac": "Lácteos e Derivados",
    "Oli": "Óleos, Azeites e Vinagres",
    "MolCo": "Molhos e Condimentos",
    "Fr": "Frutas",
    "Le": "Legumes",
    "Pr": "Proteínas"
  }

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild('myInput') input!: ElementRef;
  @ViewChild('arquivoSolicitacaoInput') arquivoSolicitacaoInput!: ElementRef<HTMLInputElement>;
  @ViewChild('fecharModalInternoBtn') fecharModalInternoBtn!: ElementRef<HTMLButtonElement>;
  @ViewChild('fecharOperacaoInternoBtn') fecharOperacaoInternoBtn!: ElementRef<HTMLButtonElement>;
  @ViewChild('fecharEdicaoEmpenhoBtn') fecharEdicaoEmpenhoBtn!: ElementRef<HTMLButtonElement>;

  enviarPara(rota: string, id?: number) {
    if (id) {
      this.router.navigate([rota], { queryParams: { id } });
    }
    else {
      this.router.navigate([rota]);
    }
  }

  verEntregasDoEmpenho(): void {
    if (!this.empenho.id) {
      return;
    }

    this.router.navigate(['/visualizar-entregas'], {
      queryParams: { empenho_id: this.empenho.id }
    });
  }

  get codigoEmpenhoEdicaoValido(): boolean {
    return Boolean(this.empenhoEdicao.codigo?.trim());
  }

  get empenhoEdicaoValida(): boolean {
    return this.codigoEmpenhoEdicaoValido;
  }

  get empenhoEdicaoAlterada(): boolean {
    const codigoAtual = String(this.empenho?.codigo || '').trim().toUpperCase();
    const codigoEdicao = String(this.empenhoEdicao.codigo || '').trim().toUpperCase();
    return codigoEdicao !== codigoAtual;
  }

  abrirEdicaoEmpenho(): void {
    this.empenhoEdicao = {
      codigo: this.empenho?.codigo || ''
    };
    this.formSubmittedEdicaoEmpenho = false;
    this.isSavingEdicaoEmpenho = false;
    this.errorMessageEdicaoEmpenho = '';
  }

  salvarEdicaoEmpenho(): void {
    this.formSubmittedEdicaoEmpenho = true;

    if (
      this.isSavingEdicaoEmpenho ||
      !this.empenhoEdicaoValida ||
      !this.empenhoEdicaoAlterada ||
      !this.empenho.id
    ) {
      return;
    }

    const codigo = this.empenhoEdicao.codigo.trim().toUpperCase();
    this.isSavingEdicaoEmpenho = true;
    this.errorMessageEdicaoEmpenho = '';

    this.empenhoService.patch(this.empenho.id, { codigo }).subscribe({
      next: (resposta: Empenho) => {
        this.empenho = {
          ...this.empenho,
          ...resposta
        };
        this.isSavingEdicaoEmpenho = false;
        this.fecharEdicaoEmpenho();
        this.feedback.sucesso('Empenho atualizado com sucesso.');
      },
      error: (erro) => {
        this.isSavingEdicaoEmpenho = false;
        this.errorMessageEdicaoEmpenho = erro?.error?.codigo
          ? 'Já existe um empenho cadastrado com este código.'
          : 'Não foi possível salvar as alterações do empenho.';
      }
    });
  }

  tentarFecharEdicaoEmpenho(): void {
    if (this.isSavingEdicaoEmpenho) {
      return;
    }

    if (!this.empenhoEdicaoAlterada) {
      this.fecharEdicaoEmpenho();
      return;
    }

    this.feedback.confirmar({
      titulo: 'Descartar alterações?',
      mensagem: 'As alterações feitas no empenho serão perdidas.',
      textoConfirmar: 'Descartar',
      textoCancelar: 'Continuar editando',
      destrutiva: true
    }).then((confirmado) => {
      if (confirmado) {
        this.fecharEdicaoEmpenho();
      }
    });
  }

  private fecharEdicaoEmpenho(): void {
    this.fecharEdicaoEmpenhoBtn?.nativeElement.click();
  }

  prepararOperacao(tipoOperacao: 'reforco' | 'anulacao'): void {
    this.tipo = tipoOperacao;
    this.operacaoItem_insercao.valor = 0;
  }

  abrirOperacao(item: ItemEmpenho, tipoOperacao: 'reforco' | 'anulacao'): void {
    this.prepararOperacao(tipoOperacao);
    this.carregarItemEmpenho(item);
    this.trocarOperacao(tipoOperacao === 'reforco' ? 'ref' : 'anl');
  }

  ngOnInit() {
    const id = Number(this.route.snapshot.queryParamMap.get('id'));

    if (!Number.isInteger(id) || id <= 0) {
      this.isLoadingPage = false;
      this.errorMessagePage = 'Não foi possível identificar o registro solicitado.';
      return;
    }

    this.idPagina = id;
    this.getEmpenho(id, true);
    this.getItensEmpenho(id);
    this.getOperacoesEmpenho(id);
    this.getSolicitacoesReforco(id);
  }

  ngAfterViewInit() {

    const modalElement = this.modal.nativeElement;

    modalElement.addEventListener('shown.bs.modal', () => {
      this.input.nativeElement.focus();
    });

    modalElement.addEventListener('hide.bs.modal', (event: Event) => {
      if (this.permitirFecharModalSemConfirmacao) {
        this.permitirFecharModalSemConfirmacao = false;
        return;
      }

      if (this.isSolicitandoEntrega) {
        event.preventDefault();
        return;
      }

      if (this.possuiDadosPreenchidosModal) {
        event.preventDefault();
        this.confirmarDescarteModalSolicitacao();
      }
    });

  }

  getEmpenho(id: number, controlarEstadoPagina: boolean = false): void {
    if (controlarEstadoPagina) {
      this.isLoadingPage = true;
      this.errorMessagePage = '';
    }

    this.empenhoService.getById(id).subscribe({
      next: (resposta: Empenho) => {
        this.empenho = resposta;
        if (controlarEstadoPagina) {
          this.isLoadingPage = false;
        }
      },
      error: () => {
        if (controlarEstadoPagina) {
          this.isLoadingPage = false;
          this.errorMessagePage = 'Não foi possível carregar este empenho no momento.';
        }
      }
    });
  }

  getItensEmpenho(id: number): void {
    this.isLoadingItens = true;
    this.errorMessageItens = '';

    this.empenhoService.itensDoEmpenho(id).subscribe({
      next: (resposta: ItemEmpenho[]) => {
        this.itensEmpenho = resposta;
      },
      complete: () => {
        this.itemEmpenhoModal = this.itensEmpenho[0];
        this.itensOrdemInsert = [];
        this.itensEmpenho.forEach(item => {
          let itemOrdemInsert = <ItemOrdemInsert>{};
          itemOrdemInsert.item_empenho = item.id;
          itemOrdemInsert.observacao = "";
          itemOrdemInsert.quantidade_entregue = 0;
          this.itensOrdemInsert.push(itemOrdemInsert);
        });
        this.itensSelecionados = new Array(this.itensEmpenho.length).fill(false);
        this.isLoadingItens = false;
      },
      error: () => {
        this.isLoadingItens = false;
        this.errorMessageItens = 'Não foi possível carregar os itens deste empenho.';
      }
    });
  }

  getOperacoesEmpenho(id: number): void {
    if (!this.pode(Recurso.OPERACAO_EMPENHO, Acao.CONSULTAR)) {
      this.isLoadingOperacoes = false;
      this.errorMessageOperacoes = '';
      this.operacoesEmpenho = [];
      return;
    }

    this.isLoadingOperacoes = true;
    this.errorMessageOperacoes = '';

    this.empenhoService.operacaoDoEmpenho(id).subscribe({
      next: (resposta: OperacaoItem[]) => {
        this.operacoesEmpenho = [...resposta].sort((operacaoA, operacaoB) => {
          const dataA = Date.parse(String(operacaoA.data)) || 0;
          const dataB = Date.parse(String(operacaoB.data)) || 0;
          return dataB - dataA;
        });
        this.isLoadingOperacoes = false;
      },
      error: () => {
        this.isLoadingOperacoes = false;
        this.errorMessageOperacoes = 'Não foi possível carregar o histórico de operações.';
      }
    });
  }

  recarregarPagina(): void {
    if (this.idPagina === null) {
      return;
    }

    this.getEmpenho(this.idPagina, true);
    this.getItensEmpenho(this.idPagina);
    this.getOperacoesEmpenho(this.idPagina);
  }

  getCategoria(item: ItemEmpenho): string {
    const categoria = this.categoria[item.item_ata.item_generico.categoria as keyof typeof this.categoria];
    return categoria ? categoria : item.item_ata.item_generico.categoria;
  }

  getTipoOperacao(tipo: string): string {
    if (tipo === 'inc') {
      return 'Inclusão';
    }
    if (tipo === 'ref') {
      return 'Reforço';
    }
    else if (tipo === 'anl') {
      return 'Anulação';
    }
    return tipo;
  }

  getClassOperacao(tipo: string): string {
    if (tipo === 'inc') {
      return 'badge bg-success';
    }
    else if (tipo === 'ref') {
      return 'badge bg-primary';
    }
    else if (tipo === 'anl') {
      return 'badge bg-danger';
    }
    return "";
  }

  onArquivoSelecionado(event: Event): void {
    const inputElement = event.target as HTMLInputElement;
    this.arquivoSolicitacao = inputElement.files && inputElement.files.length > 0
      ? inputElement.files[0]
      : null;
  }

  arredondarDuasCasas(valor: number): number {
    return Math.round((valor + Number.EPSILON) * 100) / 100;
  }

  getQuantidadeEmpenhadaMax(item: ItemEmpenho): number {
    const quantidadeEmpenhada = Number(item.quantidade_atual) || 0;
    return this.arredondarDuasCasas(quantidadeEmpenhada);
  }

  getQuantidadeDisponivelAta(item: ItemEmpenho): number {
    const quantidadeLicitada = Number(item?.item_ata?.quantidade_licitada) || 0;
    const quantidadeAtual = Number(item?.quantidade_atual) || 0;
    const quantidadeEntregue = Number(item?.quantidade_entrege) || 0;

    return this.arredondarDuasCasas(
      Math.max(quantidadeLicitada - (quantidadeAtual + quantidadeEntregue), 0)
    );
  }

  get limiteOperacaoAtual(): number {
    if (!this.itemEmpenhoModal?.id) {
      return 0;
    }

    if (this.tipo === 'reforco') {
      return this.getQuantidadeDisponivelAta(this.itemEmpenhoModal);
    }

    return this.arredondarDuasCasas(
      Math.max(Number(this.itemEmpenhoModal.quantidade_atual) || 0, 0)
    );
  }

  get operacaoValida(): boolean {
    const valor = Number(this.operacaoItem_insercao?.valor) || 0;
    return valor >= 1 && valor <= this.limiteOperacaoAtual;
  }

  get quantidadeAposOperacao(): number {
    const quantidadeAtual = Number(this.itemEmpenhoModal?.quantidade_atual) || 0;
    const valor = Number(this.operacaoItem_insercao?.valor) || 0;

    return this.tipo === 'anulacao'
      ? this.arredondarDuasCasas(quantidadeAtual - valor)
      : this.arredondarDuasCasas(quantidadeAtual + valor);
  }

  get impactoFinanceiroOperacao(): number {
    const valor = Number(this.operacaoItem_insercao?.valor) || 0;
    const valorUnitario = Number(this.itemEmpenhoModal?.item_ata?.valor_unitario) || 0;

    return this.arredondarDuasCasas(valor * valorUnitario);
  }

  validarQuantidadeSolicitada(index: number, item: ItemEmpenho): void {
    const valorAtual = this.arredondarDuasCasas(Number(this.itensOrdemInsert[index]?.quantidade_solicitada) || 0);
    const quantidadeEmpenhada = this.getQuantidadeEmpenhadaMax(item);

    if (valorAtual < 0) {
      this.itensOrdemInsert[index].quantidade_solicitada = 0;
      return;
    }

    if (valorAtual > quantidadeEmpenhada) {
      this.itensOrdemInsert[index].quantidade_solicitada = quantidadeEmpenhada;
      return;
    }

    this.itensOrdemInsert[index].quantidade_solicitada = valorAtual;
  }

  ehQuantidadeSolicitadaValida(index: number, item: ItemEmpenho): boolean {
    const quantidadeSolicitada = this.arredondarDuasCasas(
      Number(this.itensOrdemInsert[index]?.quantidade_solicitada) || 0
    );
    const quantidadeEmpenhada = this.getQuantidadeEmpenhadaMax(item);

    return quantidadeSolicitada > 0 && quantidadeSolicitada <= quantidadeEmpenhada;
  }

  calcularValorTotalItemSolicitado(item: ItemEmpenho, index: number): number {
    const quantidadeSolicitada = Number(this.itensOrdemInsert[index]?.quantidade_solicitada) || 0;
    const valorUnitario = Number(item.item_ata?.valor_unitario) || 0;

    return Number((quantidadeSolicitada * valorUnitario).toFixed(2));
  }

  calcularSomaTotalItensSolicitados(): number {
    return this.itensEmpenho.reduce((acumulador, item, index) => {
      if (!this.itensSelecionados[index]) {
        return acumulador;
      }

      const valorItem = this.calcularValorTotalItemSolicitado(item, index);
      return Number((acumulador + valorItem).toFixed(2));
    }, 0);
  }

  limparSelecao(): void {
    this.itensSelecionados = this.itensEmpenho.map(() => false);
  }

  alternarTodosItensDisponiveis(event: Event): void {
    const selecionar = (event.target as HTMLInputElement).checked;

    this.itensEmpenho.forEach((item, index) => {
      this.itensSelecionados[index] =
        Number(item.quantidade_atual) > 0
          ? selecionar
          : false;
    });
  }

  carregarItemEmpenho(item: ItemEmpenho): void {
    this.itemEmpenhoModal = item;
    this.operacaoItem_insercao.item_empenho = item.id;
    this.operacaoItem_insercao.valor = 0;
  }

  trocarOperacao(tipo: string): void {
    this.operacaoItem_insercao.tipo = tipo;
    this.operacaoItem_insercao.valor = 0;
  }

  reiniciarModalSolicitacao(): void {
    if (this.isSolicitandoEntrega) {
      return;
    }

    this.etapaSolicitacao = 1;
    this.mensagemSolicitacao = '';
    this.arquivoSolicitacao = null;
    this.ordemEntregaInsert = <OrdemEntregaInsert>{};

    this.itensOrdemInsert = this.itensEmpenho.map((item) => {
      return <ItemOrdemInsert>{
        item_empenho: item.id,
        observacao: '',
        quantidade_entregue: 0,
        quantidade_solicitada: 0
      };
    });

    if (this.arquivoSolicitacaoInput) {
      this.arquivoSolicitacaoInput.nativeElement.value = '';
    }
  }

  irParaItensSolicitacao(): void {
    if (!this.podeAvancarDadosSolicitacao) {
      return;
    }

    this.etapaSolicitacao = 2;
  }

  irParaRevisaoSolicitacao(): void {
    if (!this.podeAvancarItensSolicitacao) {
      return;
    }

    this.etapaSolicitacao = 3;
  }

  voltarEtapaSolicitacao(): void {
    if (this.isSolicitandoEntrega) {
      return;
    }

    if (this.etapaSolicitacao === 3) {
      this.etapaSolicitacao = 2;
      return;
    }

    if (this.etapaSolicitacao === 2) {
      this.etapaSolicitacao = 1;
    }
  }

  salvarOperacaoItem(): void {
    if (!this.operacaoValida) {
      return;
    }

    const tipoOperacao = this.operacaoItem_insercao.tipo;
    this.operacaoItem_insercao.data = new Date();
    this.operacaoItemService.save(this.operacaoItem_insercao).subscribe({
      next: () => {
        this.fecharModalOperacao();

        this.feedback.sucesso(
          tipoOperacao === 'ref'
            ? 'Reforço realizado com sucesso.'
            : 'Anulação realizada com sucesso.'
        );

        this.getEmpenho(this.empenho.id);
        this.getItensEmpenho(this.empenho.id);
        this.getOperacoesEmpenho(this.empenho.id);
      },
      error: (erro) => {
        const detalhe = erro?.error ? Object.values(erro.error)[0] : null;
        const mensagem =
          Array.isArray(detalhe)
            ? String(detalhe[0])
            : typeof detalhe === 'string'
              ? detalhe
              : 'Não foi possível registrar a operação.';

        this.feedback.erro(mensagem, 'Erro na operação');
      }
    });
  }

  solicitarEntrega() {
    if (this.isSolicitandoEntrega) {
      return;
    }

    if (!this.podeSolicitarEntrega) {
      this.feedback.aviso('Preencha data de previsão, anexo e quantidade válida de todos os itens selecionados.');
      return;
    }

    this.isSolicitandoEntrega = true;

    this.ordemEntregaInsert.codigo = this.gerarCodigoPedidoEntrega();
    this.ordemEntregaInsert.empenho = this.empenho.id;
    this.ordemEntregaInsert.data_emissao = new Date();
    this.ordemEntregaInsert.status = 'esp';
    this.ordemEntregaInsert.valor_total_executado = 0;

    this.ordemEntregaService.save(this.ordemEntregaInsert).subscribe({
      next: (ordemCriada: OrdemEntregaInsert) => {
        const requests = this.itensOrdemInsert
          .filter((item, index) => this.itensSelecionados[index] && Number(item.quantidade_solicitada) > 0)
          .map((item) => {
            const itemEmpenho = this.itensEmpenho.find(ie => ie.id === item.item_empenho);

            const quantidadeSolicitada = Number(item.quantidade_solicitada) || 0;
            const quantidadeJaEntregue = Number(itemEmpenho?.quantidade_entrege) || 0;
            const quantidadeEmpenhadaAtual = Number(itemEmpenho?.quantidade_atual) || 0;

            const novaQuantidadeEntregue = this.arredondarDuasCasas(
              quantidadeJaEntregue + quantidadeSolicitada
            );

            const novaQuantidadeEmpenhada = this.arredondarDuasCasas(
              Math.max(0, quantidadeEmpenhadaAtual - quantidadeSolicitada)
            );

            return this.itemOrdemService
              .save({ ...item, ordem_entrega: ordemCriada.id })
              .pipe(
                switchMap(() =>
                  this.itemEmpenhoService.patch(item.item_empenho, {
                    quantidade_entrege: novaQuantidadeEntregue,
                    quantidade_atual: novaQuantidadeEmpenhada
                  })
                )
              );
          });

        if (requests.length === 0) {
          this.acaoAposSalvarItens(ordemCriada.id);
          return;
        }

        forkJoin(requests).subscribe({
          next: () => this.acaoAposSalvarItens(ordemCriada.id),
          error: (err) => {
            this.isSolicitandoEntrega = false;
            console.error('Erro ao salvar itens da ordem', err);
            this.feedback.erro(
              'O pedido foi criado, mas não foi possível salvar todos os itens. Tente novamente.',
              'Erro ao salvar itens'
            );
          }
        });
      },
      error: (err) => {
        this.isSolicitandoEntrega = false;
        console.error('Erro ao criar ordem de entrega', err);
        this.feedback.erro(
          'Não foi possível criar o pedido de entrega. Tente novamente.',
          'Erro ao solicitar entrega'
        );
      }
    });
  }

  private acaoAposSalvarItens(ordemId: number): void {
    const formData = new FormData();
    formData.append('anexo', this.arquivoSolicitacao as File);

    if (this.mensagemSolicitacao?.trim()) {
      formData.append('corpo_mensagem', this.mensagemSolicitacao);
    }

    this.ordemEntregaService.enviarEmail(ordemId, formData).subscribe({
      next: () => {
        this.isSolicitandoEntrega = false;
        this.fecharModalSolicitacaoSemConfirmacao();
        this.feedback.sucesso('Pedido de entrega solicitado com sucesso.');
        this.getEmpenho(this.empenho.id);
        this.getItensEmpenho(this.empenho.id);
        this.limparSelecao();
      },
      error: (err) => {
        this.isSolicitandoEntrega = false;
        console.error('Erro ao enviar e-mail do pedido', err);
        this.feedback.erro(
          'O pedido foi registrado, mas não foi possível enviá-lo ao fornecedor.',
          'Erro no envio do pedido'
        );
      }
    });
  }

  tentarFecharModalSolicitacao(): void {
    if (this.isSolicitandoEntrega) {
      return;
    }

    if (this.possuiDadosPreenchidosModal) {
      this.confirmarDescarteModalSolicitacao();
      return;
    }

    this.fecharModalSolicitacaoSemConfirmacao();
  }

  private confirmarDescarteModalSolicitacao(): void {
    this.feedback.confirmar({
      titulo: 'Descartar alterações?',
      mensagem: 'Você já preencheu dados da solicitação. Se sair agora, perderá toda a operação. Deseja sair mesmo assim?',
      textoConfirmar: 'Descartar',
      textoCancelar: 'Continuar editando',
      destrutiva: true
    }).then((desejaSair) => {
      if (desejaSair) {
        this.fecharModalSolicitacaoSemConfirmacao();
      }
    });
  }

  private fecharModalSolicitacaoSemConfirmacao(): void {
    if (this.fecharModalInternoBtn?.nativeElement) {
      this.permitirFecharModalSemConfirmacao = true;
      this.fecharModalInternoBtn.nativeElement.click();
    }
  }

  private fecharModalOperacao(): void {
    this.fecharOperacaoInternoBtn?.nativeElement.click();
  }

  gerarCodigoPedidoEntrega(): string {
    const agora = new Date();
    const ano = agora.getFullYear().toString().slice(-2); // 2
    const mes = (agora.getMonth() + 1).toString().padStart(2, '0'); // 2
    const dia = agora.getDate().toString().padStart(2, '0'); // 2

    const aleatorio = Math.random()
      .toString(36)
      .toUpperCase()
      .replace(/[^A-Z0-9]/g, '')
      .slice(0, 5); // 5

    return `PED${ano}${mes}${dia}${aleatorio}`; // 13 chars
  }


}
