import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, DestroyRef, HostListener, inject, OnDestroy } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, RouteReuseStrategy, Router, RouterLink, RouterLinkActive } from "@angular/router";
import { filter, forkJoin, Observable } from 'rxjs';
import { CardapioResumo } from '../../../model/cardapio';
import { LoteValidade } from '../../../model/estoque';
import { OrdemEntrega } from '../../../model/ordem_entrega';
import { PendenciaFornecedor } from '../../../model/pendencia_fornecedor';
import { ReforcoParaPedido } from '../../../model/reforco_para_pedido';
import { SolicitacaoReforco } from '../../../model/solicitacao_reforco';
import { IdRouteReuseStrategy } from '../../../routing/id-route-reuse.strategy';
import { Auth } from '../../../service/auth';
import { CardapioService } from '../../../service/cardapio.service';
import { EstoqueService } from '../../../service/estoque.service';
import { OrdemEntregaService } from '../../../service/ordem-entrega.service';
import { PendenciaFornecedorService } from '../../../service/pendencia-fornecedor.service';
import { ReforcoParaPedidoService } from '../../../service/reforco-para-pedido.service';
import { SolicitacaoReforcoService } from '../../../service/solicitacao-reforco.service';
import { Acao, Papel, pode, Recurso } from '../../../security/rbac';

type TokenPayload = {
  papel?: string;
  username?: string;
};

@Component({
  selector: 'app-cabecalho',
  imports: [RouterLink, RouterLinkActive, DatePipe, DecimalPipe],
  templateUrl: './cabecalho.html',
  styleUrl: './cabecalho.scss',
})
export class Cabecalho implements OnDestroy {
  readonly pode = pode;
  readonly Acao = Acao;
  readonly Recurso = Recurso;

  constructor(
    private router: Router,
    private auth: Auth,
    private pendenciaService: PendenciaFornecedorService,
    private solicitacaoReforcoService: SolicitacaoReforcoService,
    private reforcoParaPedidoService: ReforcoParaPedidoService,
    private ordemEntregaService: OrdemEntregaService,
    private cardapioService: CardapioService,
    private estoqueService: EstoqueService,
  ) { }

  /** Quantos dias antes da data prevista a entrega passa a aparecer para o Estoquista. */
  readonly diasAvisoEntrega = 3;

  reforcosParaPedido: ReforcoParaPedido[] = [];
  totalReforcosParaPedido = 0;
  erroReforcosParaPedido = false;
  marcandoReforcoCienteId: number | null = null;

  entregasProximas: OrdemEntrega[] = [];
  totalEntregasProximas = 0;
  erroEntregasProximas = false;

  /** Técnico é avisado dos reforços feitos pelo Diretor para pedir a entrega ao fornecedor. */
  get podeVerReforcosParaPedido(): boolean {
    return pode(Recurso.OPERACAO_EMPENHO, Acao.GERAR_ORDEM);
  }

  /** Estoquista é avisado das entregas previstas para os próximos dias (e das atrasadas). */
  get podeVerEntregasProximas(): boolean {
    return pode(Recurso.ESTOQUE, Acao.REGISTRAR_RECEBIMENTO);
  }

  cardapiosPendentes: CardapioResumo[] = [];
  totalCardapiosPendentes = 0;
  erroCardapiosPendentes = false;

  alertasValidade: LoteValidade[] = [];
  totalAlertasValidade = 0;
  totalValidadesVencidas = 0;
  totalValidadesHoje = 0;
  totalValidadesCriticas = 0;
  totalValidadesAtencao = 0;
  erroAlertasValidade = false;

  /** Estoquista aprova retiradas e confirma consumos; Nutricionista corrige recusas e informa o consumo real. */
  get podeVerCardapios(): boolean {
    return pode(Recurso.CARDAPIO, Acao.APROVAR) || pode(Recurso.CARDAPIO, Acao.EDITAR);
  }

  get podeVerAlertasValidade(): boolean {
    return pode(Recurso.ESTOQUE, Acao.REGISTRAR_SAIDA)
      || pode(Recurso.PAINEL_NUTRICIONISTA, Acao.CONSULTAR);
  }

  get podeVerAlertas(): boolean {
    return this.podeVerPendencias || this.podeVerReforcos || this.podeVerRespostasReforco
      || this.podeVerReforcosParaPedido || this.podeVerEntregasProximas || this.podeVerCardapios
      || this.podeVerAlertasValidade;
  }

  get possuiErroAlertasVisiveis(): boolean {
    return (this.podeVerCardapios && this.erroCardapiosPendentes)
      || (this.podeVerRespostasReforco && this.erroRespostasReforco)
      || (this.podeVerReforcos && this.erroReforcos)
      || (this.podeVerReforcosParaPedido && this.erroReforcosParaPedido)
      || (this.podeVerAlertasValidade && this.erroAlertasValidade)
      || (this.podeVerEntregasProximas && this.erroEntregasProximas)
      || (this.podeVerPendencias && this.erroPendencias);
  }

  limpandoAlertas = false;
  alertasAbertos = false;
  private overflowBodyAlertasAnterior: string | null = null;

  /** Avisos que só pedem ciência (o "Ciente"/"Ok" de cada item); o botão "Limpar" dispensa todos. */
  get totalAlertasLimpaveis(): number {
    return (this.podeVerPendencias ? this.totalPendencias : 0)
      + (this.podeVerRespostasReforco ? this.totalRespostasReforco : 0)
      + (this.podeVerReforcosParaPedido ? this.totalReforcosParaPedido : 0);
  }

  limparAlertas(): void {
    const requisicoes: Observable<unknown>[] = [];
    if (this.podeVerPendencias && this.totalPendencias) {
      requisicoes.push(this.pendenciaService.limpar());
    }
    if (this.podeVerRespostasReforco && this.totalRespostasReforco) {
      requisicoes.push(this.solicitacaoReforcoService.marcarTodasVistas());
    }
    if (this.podeVerReforcosParaPedido && this.totalReforcosParaPedido) {
      requisicoes.push(this.reforcoParaPedidoService.limpar());
    }
    if (!requisicoes.length) {
      return;
    }

    this.limpandoAlertas = true;
    forkJoin(requisicoes).subscribe({
      next: () => {
        this.limpandoAlertas = false;
        this.carregarAlertas();
      },
      error: () => {
        this.limpandoAlertas = false;
        this.carregarAlertas();
      },
    });
  }

  reforcos: SolicitacaoReforco[] = [];
  totalReforcos = 0;
  erroReforcos = false;

  get podeVerPendencias(): boolean {
    return pode(Recurso.PENDENCIA_FORNECEDOR, Acao.ALTERAR_STATUS);
  }

  get podeVerReforcos(): boolean {
    return pode(Recurso.SOLICITACAO_REFORCO, Acao.REFORCAR_EMPENHO);
  }

  respostasReforco: SolicitacaoReforco[] = [];
  totalRespostasReforco = 0;
  erroRespostasReforco = false;
  marcandoVistaId: number | null = null;

  /** Quem pede reforço (Nutricionista) é avisado quando o Diretor responde. */
  get podeVerRespostasReforco(): boolean {
    return pode(Recurso.SOLICITACAO_REFORCO, Acao.CADASTRAR);
  }

  get totalAlertas(): number {
    return (this.podeVerPendencias ? this.totalPendencias : 0)
      + (this.podeVerReforcos ? this.totalReforcos : 0)
      + (this.podeVerRespostasReforco ? this.totalRespostasReforco : 0)
      + (this.podeVerReforcosParaPedido ? this.totalReforcosParaPedido : 0)
      + (this.podeVerEntregasProximas ? this.totalEntregasProximas : 0)
      + (this.podeVerCardapios ? this.totalCardapiosPendentes : 0)
      + (this.podeVerAlertasValidade ? this.totalAlertasValidade : 0);
  }

  carregarAlertas(): void {
    this.carregarPendencias();
    this.carregarReforcos();
    this.carregarRespostasReforco();
    this.carregarReforcosParaPedido();
    this.carregarEntregasProximas();
    this.carregarCardapiosPendentes();
    this.carregarAlertasValidade();
  }

  abrirAlertas(): void {
    if (this.alertasAbertos) {
      return;
    }

    this.alertasAbertos = true;
    this.bloquearScrollAlertas();
    this.carregarAlertas();
  }

  fecharAlertas(): void {
    if (!this.alertasAbertos) {
      return;
    }

    this.alertasAbertos = false;
    this.liberarScrollAlertas();
  }

  alternarAlertas(): void {
    if (this.alertasAbertos) {
      this.fecharAlertas();
      return;
    }

    this.abrirAlertas();
  }

  private bloquearScrollAlertas(): void {
    if (typeof document === 'undefined' || this.overflowBodyAlertasAnterior !== null) {
      return;
    }

    this.overflowBodyAlertasAnterior = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
  }

  private liberarScrollAlertas(): void {
    if (typeof document === 'undefined' || this.overflowBodyAlertasAnterior === null) {
      return;
    }

    document.body.style.overflow = this.overflowBodyAlertasAnterior;
    this.overflowBodyAlertasAnterior = null;
  }

  @HostListener('document:keydown.escape')
  aoPressionarEscape(): void {
    if (this.alertasAbertos) {
      this.fecharAlertas();
    }
  }

  carregarAlertasValidade(): void {
    if (!this.podeVerAlertasValidade) {
      return;
    }

    this.estoqueService.alertasValidade().subscribe({
      next: (resposta) => {
        this.alertasValidade = resposta.results;
        this.totalAlertasValidade = resposta.total;
        this.totalValidadesVencidas = resposta.vencidos;
        this.totalValidadesHoje = resposta.vence_hoje;
        this.totalValidadesCriticas = resposta.criticos;
        this.totalValidadesAtencao = resposta.atencao;
        this.erroAlertasValidade = false;
      },
      error: () => {
        this.alertasValidade = [];
        this.totalAlertasValidade = 0;
        this.totalValidadesVencidas = 0;
        this.totalValidadesHoje = 0;
        this.totalValidadesCriticas = 0;
        this.totalValidadesAtencao = 0;
        this.erroAlertasValidade = true;
      },
    });
  }

  formatarDataCivil(data: string | null): string {
    if (!data) {
      return '—';
    }
    const [ano, mes, dia] = data.split('-');
    return ano && mes && dia ? `${dia}/${mes}/${ano}` : data;
  }

  textoPrazoValidade(lote: LoteValidade): string {
    const dias = lote.dias_para_validade;
    if (dias === null) {
      return '';
    }
    if (dias < 0) {
      const quantidade = Math.abs(dias);
      return `Vencido há ${quantidade} ${quantidade === 1 ? 'dia' : 'dias'}`;
    }
    if (dias === 0) {
      return 'Vence hoje';
    }
    return `Vence em ${dias} ${dias === 1 ? 'dia' : 'dias'}`;
  }

  classeStatusValidade(lote: LoteValidade): string {
    return `alerta-status alerta-status--${lote.status.toLowerCase()}`;
  }

  carregarCardapiosPendentes(): void {
    if (!this.podeVerCardapios) {
      return;
    }

    this.cardapioService.listar({ pendentes: true }, 1, 5).subscribe({
      next: (resposta) => {
        this.cardapiosPendentes = resposta.results;
        this.totalCardapiosPendentes = resposta.count;
        this.erroCardapiosPendentes = false;
      },
      error: () => {
        this.erroCardapiosPendentes = true;
      },
    });
  }

  textoPendenciaCardapio(cardapio: CardapioResumo): string {
    switch (cardapio.status) {
      case 'ENVIADO':
        return 'Aguardando a aprovação da retirada dos gêneros.';
      case 'CONSUMO_INFORMADO':
        return 'Consumo real informado. Confira e acerte o estoque.';
      case 'ALTERACAO_SOLICITADA':
        return 'A nutricionista pediu para alterar o cardápio. Aceite para devolver os gêneros ao estoque.';
      case 'RASCUNHO':
        return 'Alteração aceita pelo estoque. Ajuste o novo rascunho e reenvie.';
      case 'RECUSADO':
        return 'Retirada recusada pelo estoque. Corrija e reenvie.';
      case 'APROVADO':
        if (!cardapio.motivo_recusa) {
          return 'Retirada aprovada. Após o preparo, informe o consumo real.';
        }
        return cardapio.motivo_alteracao
          ? 'Pedido de alteração recusado pelo estoque.'
          : 'Consumo devolvido pelo estoque para correção.';
      default:
        return cardapio.status_descricao;
    }
  }

  carregarReforcosParaPedido(): void {
    if (!this.podeVerReforcosParaPedido) {
      return;
    }

    this.reforcoParaPedidoService.listar(1, 5).subscribe({
      next: (resposta) => {
        this.reforcosParaPedido = resposta.results;
        this.totalReforcosParaPedido = resposta.count;
        this.erroReforcosParaPedido = false;
      },
      error: () => {
        this.erroReforcosParaPedido = true;
      },
    });
  }

  marcarReforcoCiente(reforco: ReforcoParaPedido): void {
    this.marcandoReforcoCienteId = reforco.id;
    this.reforcoParaPedidoService.marcarCiente(reforco.id).subscribe({
      next: () => {
        this.marcandoReforcoCienteId = null;
        this.carregarReforcosParaPedido();
      },
      error: () => {
        this.marcandoReforcoCienteId = null;
        this.erroReforcosParaPedido = true;
      },
    });
  }

  carregarEntregasProximas(): void {
    if (!this.podeVerEntregasProximas) {
      return;
    }

    const limite = new Date();
    limite.setDate(limite.getDate() + this.diasAvisoEntrega);
    limite.setHours(23, 59, 59, 999);

    this.ordemEntregaService.get('', 1, 5, {
      status__in: 'esp,par',
      data_entrega_prevista__lte: limite.toISOString(),
      ordering: 'data_entrega_prevista',
    }).subscribe({
      next: (resposta) => {
        this.entregasProximas = resposta.results;
        this.totalEntregasProximas = resposta.count;
        this.erroEntregasProximas = false;
      },
      error: () => {
        this.erroEntregasProximas = true;
      },
    });
  }

  entregaAtrasada(ordem: OrdemEntrega): boolean {
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    return new Date(ordem.data_entrega_prevista) < hoje;
  }

  carregarRespostasReforco(): void {
    if (!this.podeVerRespostasReforco) {
      return;
    }

    this.solicitacaoReforcoService.listar({ naoVistas: true }, 1, 5).subscribe({
      next: (resposta) => {
        this.respostasReforco = resposta.results;
        this.totalRespostasReforco = resposta.count;
        this.erroRespostasReforco = false;
      },
      error: () => {
        this.erroRespostasReforco = true;
      },
    });
  }

  marcarRespostaVista(resposta: SolicitacaoReforco): void {
    this.marcandoVistaId = resposta.id;
    this.solicitacaoReforcoService.marcarVista(resposta.id).subscribe({
      next: () => {
        this.marcandoVistaId = null;
        this.carregarRespostasReforco();
      },
      error: () => {
        this.marcandoVistaId = null;
        this.erroRespostasReforco = true;
      },
    });
  }

  carregarReforcos(): void {
    if (!this.podeVerReforcos) {
      return;
    }

    this.solicitacaoReforcoService.listar({ status: 'PENDENTE' }, 1, 5).subscribe({
      next: (resposta) => {
        this.reforcos = resposta.results;
        this.totalReforcos = resposta.count;
        this.erroReforcos = false;
      },
      error: () => {
        this.erroReforcos = true;
      },
    });
  }

  papel: string = "";
  usuario: string = "";

  pendencias: PendenciaFornecedor[] = [];
  totalPendencias = 0;
  erroPendencias = false;
  marcandoCiente: number | null = null;

  readonly rotasAquisicoes = [
    '/visualizar-licitacoes',
    '/visualizar-licitacao',
    '/adicionar-licitacao',
    '/visualizar-atas',
    '/visualizar-ata',
    '/visualizar-empenhos',
    '/visualizar-empenho',
  ] as const;

  readonly rotasCardapios = ['/cardapios', '/cardapio'] as const;

  readonly rotasCadastros = [
    '/visualizar-fornecedores',
    '/visualizar-fornecedor',
    '/visualizar-gens-alimenticios',
    '/visualizar-gen-alimenticio',
  ] as const;

  realizarLogout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  getPayload(): TokenPayload | null {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    try {
      return JSON.parse(atob(token.split('.')[1])) as TokenPayload;
    } catch {
      return null;
    }
  }

  getPapel(): void {
    this.papel = this.getPayload()?.papel ?? '';
  }

  getUser(): void {
    this.usuario = this.getPayload()?.username ?? '';
  }


  ngOnInit() {
    this.getPapel();
    this.getUser();
    this.carregarAlertas();

    // O cabeçalho vive durante toda a sessão: atualiza as notificações a cada troca de tela.
    this.router.events
      .pipe(filter(evento => evento instanceof NavigationEnd), takeUntilDestroyed(this.destroyRef))
      .subscribe(() => {
        this.fecharAlertas();
        this.carregarAlertas();
      });
  }

  ngOnDestroy(): void {
    this.alertasAbertos = false;
    this.liberarScrollAlertas();
  }

  private readonly destroyRef = inject(DestroyRef);
  private readonly reuseStrategy = inject(RouteReuseStrategy);

  /**
   * O routerLink ignora o clique quando a notificação aponta para a tela já aberta,
   * e ela continuaria com dados antigos (ex.: reforço novo no empenho que está aberto).
   * Nesse caso a tela é recriada para buscar os dados de novo.
   */
  reabrirSeJaAberta(rota: string, id: number): void {
    this.fecharAlertas();

    const destino = this.router.createUrlTree([rota], { queryParams: { id } });
    if (this.router.url !== this.router.serializeUrl(destino)) {
      return;
    }

    if (this.reuseStrategy instanceof IdRouteReuseStrategy) {
      this.reuseStrategy.recriarNaProximaNavegacao();
    }
    this.router.navigateByUrl(destino, { onSameUrlNavigation: 'reload' });
  }

  carregarPendencias(): void {
    if (!this.podeVerPendencias) {
      return;
    }

    this.pendenciaService.listar('ABERTA', 1, 5).subscribe({
      next: (resposta) => {
        this.pendencias = resposta.results;
        this.totalPendencias = resposta.count;
        this.erroPendencias = false;
      },
      error: () => {
        this.erroPendencias = true;
      },
    });
  }

  marcarCiente(pendencia: PendenciaFornecedor): void {
    this.marcandoCiente = pendencia.id;
    this.pendenciaService.marcarCiente(pendencia.id).subscribe({
      next: () => {
        this.marcandoCiente = null;
        this.carregarPendencias();
      },
      error: () => {
        this.marcandoCiente = null;
        this.erroPendencias = true;
      },
    });
  }

  verificarPapel(papel: string): string {
    if (papel === Papel.DIRETOR) {
      return 'Diretor';
    }
    if (papel === Papel.NUTRICIONISTA) {
      return 'Nutricionista';
    }
    if (papel === Papel.ESTOQUISTA) {
      return 'Estoquista';
    }
    return 'Técnico Administrativo';
  }

  isGrupoAtivo(rotas: readonly string[]): boolean {
    const caminhoAtual = this.router.url.split(/[?#]/)[0];

    return rotas.some(
      rota => caminhoAtual === rota || caminhoAtual.startsWith(`${rota}/`)
    );
  }

}

