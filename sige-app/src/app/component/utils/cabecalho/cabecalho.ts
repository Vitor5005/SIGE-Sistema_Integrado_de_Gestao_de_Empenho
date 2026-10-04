import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, DestroyRef, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterLinkActive } from "@angular/router";
import { filter } from 'rxjs';
import { OrdemEntrega } from '../../../model/ordem_entrega';
import { PendenciaFornecedor } from '../../../model/pendencia_fornecedor';
import { ReforcoParaPedido } from '../../../model/reforco_para_pedido';
import { SolicitacaoReforco } from '../../../model/solicitacao_reforco';
import { Auth } from '../../../service/auth';
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
export class Cabecalho {
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

  get podeVerAlertas(): boolean {
    return this.podeVerPendencias || this.podeVerReforcos || this.podeVerRespostasReforco
      || this.podeVerReforcosParaPedido || this.podeVerEntregasProximas;
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
      + (this.podeVerEntregasProximas ? this.totalEntregasProximas : 0);
  }

  carregarAlertas(): void {
    this.carregarPendencias();
    this.carregarReforcos();
    this.carregarRespostasReforco();
    this.carregarReforcosParaPedido();
    this.carregarEntregasProximas();
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
      .subscribe(() => this.carregarAlertas());
  }

  private readonly destroyRef = inject(DestroyRef);

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

