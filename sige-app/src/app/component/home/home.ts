import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { catchError, forkJoin, Observable, of } from 'rxjs';
import { Ata } from '../../model/ata';
import { Empenho } from '../../model/empenho';
import { Licitacao } from '../../model/licitacao';
import { OrdemEntrega } from '../../model/ordem_entrega';
import { PaginatedResponse } from '../../model/pagination';
import { AtaService } from '../../service/ata.service';
import { EmpenhoService, ResumoFinanceiroEmpenhos } from '../../service/empenho.service';
import { LicitacaoService } from '../../service/licitacao.service';
import { OrdemEntregaService } from '../../service/ordem-entrega.service';
import { Acao, pode, Recurso } from '../../security/rbac';
import { PainelNutricionista } from './painel-nutricionista/painel-nutricionista';

type IndicadorKey = 'licitacoes' | 'arps' | 'empenhos' | 'entregasEmEspera';
type ContextoDados = 'atual' | 'todas';
type PerfilOperacional = 'diretor' | 'tecnico' | 'nutricionista' | 'estoquista';

interface EstadoIndicador {
  valor: number | null;
  carregando: boolean;
  erro: boolean;
}

@Component({
  selector: 'app-home',
  imports: [CommonModule, RouterLink, PainelNutricionista],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home implements OnInit {
  readonly pode = pode;
  readonly Acao = Acao;
  readonly Recurso = Recurso;

  readonly podeVerLicitacoes = pode(Recurso.LICITACAO, Acao.CONSULTAR);
  readonly podeVerAtas = pode(Recurso.ATA, Acao.CONSULTAR);
  readonly podeVerEmpenhos = pode(Recurso.EMPENHO, Acao.CONSULTAR);
  readonly podeVerPainelNutricionista = pode(Recurso.PAINEL_NUTRICIONISTA, Acao.CONSULTAR);

  indicadores: Record<IndicadorKey, EstadoIndicador> = {
    licitacoes: { valor: null, carregando: true, erro: false },
    arps: { valor: null, carregando: true, erro: false },
    empenhos: { valor: null, carregando: true, erro: false },
    entregasEmEspera: { valor: null, carregando: true, erro: false },
  };

  licitacaoAtual: Licitacao | null = null;
  contextoDados: ContextoDados = 'todas';
  carregandoContexto = true;
  erroContexto = false;

  totalEntregasAtrasadas: number | null = null;
  carregandoAtencao = true;
  erroAtencao = false;

  totalEntregasAtrasadasContexto: number | null = null;
  carregandoAtrasosContextuais = false;
  erroAtrasosContextuais = false;

  totalEntregasConcluidas: number | null = null;
  carregandoGraficoEntregas = true;
  erroGraficoEntregas = false;

  resumoFinanceiro: ResumoFinanceiroEmpenhos | null = null;
  carregandoResumoFinanceiro = true;
  erroResumoFinanceiro = false;

  entregasRecentes: OrdemEntrega[] = [];
  carregandoEntregasRecentes = true;
  erroEntregasRecentes = false;

  private versaoContexto = 0;

  private readonly formatadorMoeda = new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });

  constructor(
    private licitacaoService: LicitacaoService,
    private ataService: AtaService,
    private empenhoService: EmpenhoService,
    private ordemEntregaService: OrdemEntregaService,
  ) {}

  ngOnInit(): void {
    this.carregarAtrasosGlobais();

    if (this.podeVerLicitacoes) {
      this.carregarContextoInicial();
      return;
    }

    // Sem acesso às licitações (ex.: Estoquista): exibe apenas dados de todas as entregas.
    this.carregandoContexto = false;
    this.carregarDadosDoContexto();
  }

  selecionarContexto(contexto: ContextoDados): void {
    if (contexto === 'atual' && !this.licitacaoAtual) {
      return;
    }

    if (this.contextoDados === contexto) {
      return;
    }

    this.contextoDados = contexto;
    this.carregarDadosDoContexto();
  }

  get usandoLicitacaoAtual(): boolean {
    return this.contextoDados === 'atual' && this.licitacaoAtual !== null;
  }

  get perfilOperacional(): PerfilOperacional {
    if (this.pode(Recurso.LICITACAO, Acao.CADASTRAR)) {
      return 'diretor';
    }

    if (this.pode(Recurso.ORDEM_ENTREGA, Acao.GERAR_ORDEM)) {
      return 'tecnico';
    }

    if (this.pode(Recurso.ESTOQUE, Acao.REGISTRAR_SAIDA)) {
      return 'estoquista';
    }

    return 'nutricionista';
  }

  get descricaoPerfil(): string {
    switch (this.perfilOperacional) {
      case 'diretor':
        return 'Acompanhe aquisições, empenhos, entregas e atividades administrativas.';
      case 'tecnico':
        return 'Acompanhe empenhos, ordens de entrega e pendências operacionais.';
      case 'estoquista':
        return 'Acompanhe recebimentos, movimentações e disponibilidade do estoque.';
      default:
        return 'Consulte aquisições, entregas e disponibilidade dos gêneros alimentícios.';
    }
  }

  get atrasosOutrasLicitacoes(): number {
    if (this.totalEntregasAtrasadas === null || this.totalEntregasAtrasadasContexto === null) {
      return 0;
    }

    return Math.max(0, this.totalEntregasAtrasadas - this.totalEntregasAtrasadasContexto);
  }

  get quantidadeEntregasEmEsperaGrafico(): number {
    return this.indicadores.entregasEmEspera.valor ?? 0;
  }

  get quantidadeEntregasConcluidasGrafico(): number {
    return this.totalEntregasConcluidas ?? 0;
  }

  get totalEntregasGrafico(): number {
    return this.quantidadeEntregasConcluidasGrafico + this.quantidadeEntregasEmEsperaGrafico;
  }

  get percentualEntregasConcluidas(): number {
    return this.calcularPercentual(
      this.quantidadeEntregasConcluidasGrafico,
      this.totalEntregasGrafico,
    );
  }

  get percentualEntregasEmEspera(): number {
    return this.calcularPercentual(
      this.quantidadeEntregasEmEsperaGrafico,
      this.totalEntregasGrafico,
    );
  }

  get valorEmpenhado(): number {
    return this.normalizarValorFinanceiro(this.resumoFinanceiro?.valor_empenhado);
  }

  get valorUtilizado(): number {
    return this.normalizarValorFinanceiro(this.resumoFinanceiro?.valor_utilizado);
  }

  get valorDisponivel(): number {
    return this.normalizarValorFinanceiro(this.resumoFinanceiro?.valor_disponivel);
  }

  get possuiResumoFinanceiro(): boolean {
    return this.valorEmpenhado > 0;
  }

  get percentualUtilizado(): number {
    return this.calcularPercentual(this.valorUtilizado, this.valorEmpenhado);
  }

  get percentualDisponivel(): number {
    return this.calcularPercentual(this.valorDisponivel, this.valorEmpenhado);
  }

  get larguraPercentualUtilizado(): number {
    return this.limitarPercentual(this.percentualUtilizado);
  }

  get larguraPercentualDisponivel(): number {
    return this.limitarPercentual(this.percentualDisponivel);
  }

  textoStatusEntrega(entrega: OrdemEntrega): string {
    if (this.estaAtrasada(entrega)) {
      return 'Atrasada';
    }

    if (entrega.status === 'con') {
      return 'Concluída';
    }

    if (entrega.status === 'esp') {
      return 'Em espera';
    }

    if (entrega.status === 'par') {
      return 'Parcialmente entregue';
    }

    return entrega.status;
  }

  estaAtrasada(entrega: OrdemEntrega): boolean {
    if (entrega.status === 'con' || !entrega.data_entrega_prevista) {
      return false;
    }

    const dataPrevista = new Date(entrega.data_entrega_prevista).getTime();
    return !Number.isNaN(dataPrevista) && dataPrevista < Date.now();
  }

  formatarMoeda(valor: number | string | null | undefined): string {
    if (valor === null || valor === undefined || valor === '') {
      return '—';
    }

    const valorNumerico = Number(valor);
    return Number.isFinite(valorNumerico) ? this.formatadorMoeda.format(valorNumerico) : '—';
  }

  formatarPercentual(percentual: number): string {
    return `${Math.round(percentual)}%`;
  }

  private carregarContextoInicial(): void {
    this.licitacaoService
      .getAtual()
      .pipe(
        catchError(() => {
          this.erroContexto = true;
          return of(null);
        }),
      )
      .subscribe((licitacao) => {
        this.licitacaoAtual = licitacao;
        this.contextoDados = licitacao ? 'atual' : 'todas';
        this.carregandoContexto = false;
        this.carregarDadosDoContexto();
      });
  }

  private carregarDadosDoContexto(): void {
    const versao = ++this.versaoContexto;
    const licitacaoId = this.usandoLicitacaoAtual ? this.licitacaoAtual?.id ?? null : null;

    this.prepararIndicadoresParaCarregamento();
    this.prepararGraficoEntregasParaCarregamento();
    this.carregarIndicadores(licitacaoId, versao);
    this.carregarResumoFinanceiro(licitacaoId, versao);
    this.carregarEntregasRecentes(licitacaoId, versao);

    if (licitacaoId !== null) {
      this.carregarAtrasosContextuais(licitacaoId, versao);
      return;
    }

    this.totalEntregasAtrasadasContexto = null;
    this.carregandoAtrasosContextuais = false;
    this.erroAtrasosContextuais = false;
  }

  private prepararIndicadoresParaCarregamento(): void {
    Object.values(this.indicadores).forEach((indicador) => {
      indicador.valor = null;
      indicador.carregando = true;
      indicador.erro = false;
    });
  }

  private prepararGraficoEntregasParaCarregamento(): void {
    this.totalEntregasConcluidas = null;
    this.carregandoGraficoEntregas = true;
    this.erroGraficoEntregas = false;
  }

  private carregarIndicadores(licitacaoId: number | null, versao: number): void {
    const filtrosAta = licitacaoId === null ? {} : { licitacao__id: licitacaoId };
    const filtrosEmpenho = licitacaoId === null ? {} : { ata__licitacao__id: licitacaoId };
    const filtrosEntregas = licitacaoId === null
      ? { status: 'esp' }
      : { status: 'esp', empenho__ata__licitacao__id: licitacaoId };
    const filtrosEntregasConcluidas = licitacaoId === null
      ? { status: 'con' }
      : { status: 'con', empenho__ata__licitacao__id: licitacaoId };

    const consultasContextuais = {
      arps: this.podeVerAtas
        ? this.consultaSegura(this.ataService.get(filtrosAta, 1, 1))
        : of(null),
      empenhos: this.podeVerEmpenhos
        ? this.consultaSegura(this.empenhoService.get('', 1, 1, filtrosEmpenho))
        : of(null),
      entregasEmEspera: this.consultaSegura(
        this.ordemEntregaService.get('', 1, 1, filtrosEntregas),
      ),
      entregasConcluidas: this.consultaSegura(
        this.ordemEntregaService.get('', 1, 1, filtrosEntregasConcluidas),
      ),
    };

    if (licitacaoId !== null) {
      const indicadorLicitacoes = this.indicadores.licitacoes;
      indicadorLicitacoes.valor = 1;
      indicadorLicitacoes.carregando = false;
      indicadorLicitacoes.erro = false;

      forkJoin(consultasContextuais).subscribe(({ arps, empenhos, entregasEmEspera, entregasConcluidas }) => {
        if (versao !== this.versaoContexto) {
          return;
        }

        this.atualizarIndicador('arps', arps);
        this.atualizarIndicador('empenhos', empenhos);
        this.atualizarIndicador('entregasEmEspera', entregasEmEspera);
        this.atualizarGraficoEntregas(entregasConcluidas, entregasEmEspera);
      });
      return;
    }

    forkJoin({
      licitacoes: this.podeVerLicitacoes
        ? this.consultaSegura(this.licitacaoService.get('', 1, 1))
        : of(null),
      ...consultasContextuais,
    }).subscribe(({ licitacoes, arps, empenhos, entregasEmEspera, entregasConcluidas }) => {
      if (versao !== this.versaoContexto) {
        return;
      }

      this.atualizarIndicador('licitacoes', licitacoes);
      this.atualizarIndicador('arps', arps);
      this.atualizarIndicador('empenhos', empenhos);
      this.atualizarIndicador('entregasEmEspera', entregasEmEspera);
      this.atualizarGraficoEntregas(entregasConcluidas, entregasEmEspera);
    });
  }

  private atualizarGraficoEntregas(
    entregasConcluidas: PaginatedResponse<OrdemEntrega> | null,
    entregasEmEspera: PaginatedResponse<OrdemEntrega> | null,
  ): void {
    this.totalEntregasConcluidas = entregasConcluidas?.count ?? null;
    this.erroGraficoEntregas = entregasConcluidas === null || entregasEmEspera === null;
    this.carregandoGraficoEntregas = false;
  }

  private carregarResumoFinanceiro(licitacaoId: number | null, versao: number): void {
    this.resumoFinanceiro = null;
    this.carregandoResumoFinanceiro = this.podeVerEmpenhos;
    this.erroResumoFinanceiro = false;

    if (!this.podeVerEmpenhos) {
      return;
    }

    this.empenhoService
      .getResumoFinanceiro(licitacaoId)
      .pipe(catchError(() => of(null)))
      .subscribe((resumo) => {
        if (versao !== this.versaoContexto) {
          return;
        }

        this.resumoFinanceiro = resumo;
        this.erroResumoFinanceiro = resumo === null;
        this.carregandoResumoFinanceiro = false;
      });
  }

  private carregarAtrasosGlobais(): void {
    const agora = new Date().toISOString();

    this.consultaSegura(
      this.ordemEntregaService.get('', 1, 1, {
        status: 'esp',
        data_entrega_prevista__lte: agora,
      }),
    ).subscribe((entregasAtrasadas) => {
      this.totalEntregasAtrasadas = entregasAtrasadas?.count ?? null;
      this.erroAtencao = entregasAtrasadas === null;
      this.carregandoAtencao = false;
    });
  }

  private carregarAtrasosContextuais(licitacaoId: number, versao: number): void {
    const agora = new Date().toISOString();

    this.totalEntregasAtrasadasContexto = null;
    this.carregandoAtrasosContextuais = true;
    this.erroAtrasosContextuais = false;

    this.consultaSegura(
      this.ordemEntregaService.get('', 1, 1, {
        status: 'esp',
        data_entrega_prevista__lte: agora,
        empenho__ata__licitacao__id: licitacaoId,
      }),
    ).subscribe((entregasAtrasadas) => {
      if (versao !== this.versaoContexto) {
        return;
      }

      this.totalEntregasAtrasadasContexto = entregasAtrasadas?.count ?? null;
      this.erroAtrasosContextuais = entregasAtrasadas === null;
      this.carregandoAtrasosContextuais = false;
    });
  }

  private carregarEntregasRecentes(licitacaoId: number | null, versao: number): void {
    const filtros = licitacaoId === null ? {} : { empenho__ata__licitacao__id: licitacaoId };

    this.entregasRecentes = [];
    this.carregandoEntregasRecentes = true;
    this.erroEntregasRecentes = false;

    this.consultaSegura(this.ordemEntregaService.get('', 1, 5, filtros)).subscribe((resposta) => {
      if (versao !== this.versaoContexto) {
        return;
      }

      this.entregasRecentes = resposta?.results ?? [];
      this.erroEntregasRecentes = resposta === null;
      this.carregandoEntregasRecentes = false;
    });
  }

  private atualizarIndicador<T>(
    chave: IndicadorKey,
    resposta: PaginatedResponse<T> | null,
  ): void {
    const indicador = this.indicadores[chave];
    indicador.valor = resposta?.count ?? null;
    indicador.erro = resposta === null;
    indicador.carregando = false;
  }

  private consultaSegura<T>(
    consulta: Observable<PaginatedResponse<T>>,
  ): Observable<PaginatedResponse<T> | null> {
    return consulta.pipe(catchError(() => of(null)));
  }

  private calcularPercentual(parte: number, total: number): number {
    return total > 0 ? (parte / total) * 100 : 0;
  }

  private limitarPercentual(percentual: number): number {
    return Math.min(100, Math.max(0, percentual));
  }

  private normalizarValorFinanceiro(valor: number | string | undefined): number {
    const valorNumerico = Number(valor);
    return Number.isFinite(valorNumerico) ? valorNumerico : 0;
  }
}
