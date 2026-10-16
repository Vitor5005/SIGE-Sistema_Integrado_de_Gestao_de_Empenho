import { DatePipe } from '@angular/common';
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Observable } from 'rxjs';

import {
  Cardapio,
  CardapioInsert,
  DisponibilidadeGenero,
  ItemCardapio,
  REFEICOES,
  RefeicaoCardapio,
} from '../../../model/cardapio';
import { OpcaoReforcoGenero } from '../../../model/solicitacao_reforco';
import { Acao, obterNomeUsuarioAtual, pode, Recurso } from '../../../security/rbac';
import { CardapioService, mensagemErroCardapio } from '../../../service/cardapio.service';
import { FeedbackService } from '../../../service/feedback.service';
import { SolicitacaoReforcoService } from '../../../service/solicitacao-reforco.service';
import { BotaoVoltar } from '../../utils/botao-voltar/botao-voltar';
import { EstadoConteudo } from '../../utils/estado-conteudo/estado-conteudo';
import { CardapioDocumento } from '../cardapio-documento/cardapio-documento';
import { agruparPorSecao, formatarQuantidade, unidadeComEmbalagem } from '../cardapio-util';

/** Abaixo desta fração do saldo disponível restante, o gênero recebe o aviso de estoque baixo. */
const FRACAO_ESTOQUE_BAIXO = 0.2;

interface LinhaForm {
  item_generico: number | null;
  quantidade: number | null;
  observacao: string;
}

interface SecaoForm {
  titulo: string;
  linhas: LinhaForm[];
}

/** Efeito de um gênero do cardápio sobre o saldo disponível, exibido na revisão. */
interface ImpactoEstoque {
  genero: DisponibilidadeGenero;
  quantidade: number;
  restante: number;
  estoqueBaixo: boolean;
}

/** Pedido de reforço ao Diretor aberto a partir de um gênero com estoque baixo. */
interface PedidoReforco {
  linha: LinhaForm;
  genero: DisponibilidadeGenero;
  opcoes: OpcaoReforcoGenero[];
  carregando: boolean;
  itemEmpenho: number | null;
  quantidade: number | null;
  justificativa: string;
  enviando: boolean;
  erro: string;
}

@Component({
  selector: 'app-cardapio-form',
  imports: [BotaoVoltar, CardapioDocumento, DatePipe, EstadoConteudo, FormsModule, RouterLink],
  templateUrl: './cardapio-form.html',
  styleUrl: './cardapio-form.scss',
})
export class CardapioForm implements OnInit {
  readonly refeicoes = REFEICOES;
  readonly formatarQuantidade = formatarQuantidade;
  readonly unidadeComEmbalagem = unidadeComEmbalagem;

  id: number | null = null;
  motivoRecusa = '';
  carregando = true;
  erroCarregamento = '';
  salvando = false;
  formSubmitted = false;
  erro = '';

  refeicao: RefeicaoCardapio | '' = '';
  data = this.hoje();
  /** Data já gravada do rascunho em edição; continua aceita mesmo que já tenha passado. */
  private dataOriginal = '';
  estimativaPessoas: number | null = null;
  preparacoes = '';
  observacoes = '';
  secoes: SecaoForm[] = [{ titulo: '', linhas: [this.linhaVazia()] }];

  disponibilidade: DisponibilidadeGenero[] = [];
  disponibilidadeCarregada = false;
  /** Linhas cuja quantidade foi reduzida automaticamente ao saldo disponível. */
  private linhasAjustadas = new WeakSet<LinhaForm>();
  private disponibilidadePorGenero = new Map<number, DisponibilidadeGenero>();

  reforco: PedidoReforco | null = null;

  /** Etapa de conferência antes de salvar e enviar o cardápio ao estoque. */
  emRevisao = false;
  previa: Cardapio | null = null;
  impactoEstoque: ImpactoEstoque[] = [];
  private nomeNutricionista = obterNomeUsuarioAtual();

  @ViewChild('tituloRevisao') tituloRevisao?: ElementRef<HTMLElement>;

  constructor(
    private cardapioService: CardapioService,
    private solicitacaoReforcoService: SolicitacaoReforcoService,
    private feedback: FeedbackService,
    private route: ActivatedRoute,
    private router: Router,
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.queryParamMap.get('id'));
    this.id = Number.isInteger(id) && id > 0 ? id : null;
    this.carregarDisponibilidade();

    if (!this.id) {
      this.carregando = false;
      return;
    }

    this.cardapioService.obter(this.id).subscribe({
      next: (cardapio) => {
        if (!['RASCUNHO', 'RECUSADO'].includes(cardapio.status)) {
          this.router.navigate(['/cardapio'], { queryParams: { id: cardapio.id } });
          return;
        }
        this.preencher(cardapio);
        this.carregando = false;
      },
      error: () => {
        this.erroCarregamento = 'Não foi possível carregar o cardápio.';
        this.carregando = false;
      },
    });
  }

  get modoEdicao(): boolean {
    return this.id !== null;
  }

  /** Hoje no formato do campo de data (aaaa-mm-dd), no fuso do navegador. */
  hoje(): string {
    const agora = new Date();
    return [
      agora.getFullYear(),
      String(agora.getMonth() + 1).padStart(2, '0'),
      String(agora.getDate()).padStart(2, '0'),
    ].join('-');
  }

  private linhaVazia(): LinhaForm {
    return { item_generico: null, quantidade: null, observacao: '' };
  }

  private carregarDisponibilidade(): void {
    this.cardapioService.disponibilidade(this.id ?? undefined).subscribe({
      next: (dados) => {
        // Gêneros com saldo primeiro; os zerados aparecem no fim, desabilitados.
        this.disponibilidade = [...dados].sort((a, b) =>
          Number(Number(b.disponivel) > 0) - Number(Number(a.disponivel) > 0)
          || a.descricao.localeCompare(b.descricao));
        this.disponibilidadePorGenero = new Map(dados.map((item) => [item.item_generico_id, item]));
        this.disponibilidadeCarregada = true;
      },
      error: () => {
        this.erro = 'Não foi possível consultar os saldos do estoque. Tente recarregar a página.';
      },
    });
  }

  private preencher(cardapio: Cardapio): void {
    this.refeicao = cardapio.refeicao;
    this.data = cardapio.data;
    this.dataOriginal = cardapio.data;
    this.estimativaPessoas = cardapio.estimativa_pessoas;
    this.preparacoes = cardapio.preparacoes;
    this.observacoes = cardapio.observacoes;
    this.motivoRecusa = cardapio.status === 'RECUSADO' ? cardapio.motivo_recusa : '';
    this.nomeNutricionista = cardapio.criado_por_nome || this.nomeNutricionista;

    const grupos = agruparPorSecao(cardapio.itens);
    this.secoes = grupos.length
      ? grupos.map((grupo) => ({
        titulo: grupo.secao,
        linhas: grupo.itens.map((item) => ({
          item_generico: item.item_generico,
          quantidade: Number(item.quantidade_planejada),
          observacao: item.observacao,
        })),
      }))
      : [{ titulo: '', linhas: [this.linhaVazia()] }];

    // A primeira seção é sempre a das preparações principais (sem título).
    if (this.secoes[0].titulo) {
      this.secoes.unshift({ titulo: '', linhas: [] });
    }
  }

  // ---- Seções e linhas do detalhamento ----

  adicionarLinha(secao: SecaoForm): void {
    secao.linhas.push(this.linhaVazia());
  }

  removerLinha(secao: SecaoForm, indice: number): void {
    secao.linhas.splice(indice, 1);
  }

  adicionarSecao(): void {
    this.secoes.push({ titulo: '', linhas: [this.linhaVazia()] });
  }

  removerSecao(indice: number): void {
    this.secoes.splice(indice, 1);
  }

  // ---- Saldos ----

  generoDe(id: number | null): DisponibilidadeGenero | undefined {
    return id ? this.disponibilidadePorGenero.get(Number(id)) : undefined;
  }

  totalPlanejado(generoId: number | null): number {
    if (!generoId) {
      return 0;
    }
    return this.secoes
      .flatMap((secao) => secao.linhas)
      .filter((linha) => Number(linha.item_generico) === Number(generoId))
      .reduce((total, linha) => total + (Number(linha.quantidade) || 0), 0);
  }

  excedeSaldo(generoId: number | null): boolean {
    const genero = this.generoDe(generoId);
    return Boolean(genero) && this.totalPlanejado(generoId) > Number(genero!.disponivel) + 0.0005;
  }

  get generosComSaldo(): DisponibilidadeGenero[] {
    return this.disponibilidade.filter((genero) => Number(genero.disponivel) > 0);
  }

  /** Não há o que planejar: nenhum gênero tem saldo disponível no estoque. */
  get semEstoque(): boolean {
    return this.disponibilidadeCarregada && this.generosComSaldo.length === 0;
  }

  generoSemSaldo(generoId: number | null): boolean {
    const genero = this.generoDe(generoId);
    return Boolean(genero) && Number(genero!.disponivel) <= 0;
  }

  /** Máximo que a linha pode usar: o disponível menos o que as outras linhas do mesmo gênero já usam. */
  maximoDaLinha(linha: LinhaForm): number {
    const genero = this.generoDe(linha.item_generico);
    if (!genero) {
      return 0;
    }
    const outrasLinhas = this.totalPlanejado(linha.item_generico) - (Number(linha.quantidade) || 0);
    return Math.max(this.arredondar(Number(genero.disponivel) - outrasLinhas), 0);
  }

  /** Mantém a quantidade dentro do saldo: o que passar do disponível é reduzido ao máximo. */
  ajustarAoSaldo(linha: LinhaForm): void {
    this.linhasAjustadas.delete(linha);
    if (!linha.item_generico || linha.quantidade === null || linha.quantidade === undefined) {
      return;
    }
    const maximo = this.maximoDaLinha(linha);
    if (Number(linha.quantidade) > maximo) {
      linha.quantidade = maximo > 0 ? maximo : null;
      this.linhasAjustadas.add(linha);
    }
  }

  foiAjustada(linha: LinhaForm): boolean {
    return this.linhasAjustadas.has(linha);
  }

  /** Quanto do gênero sobra no estoque disponível depois deste cardápio. */
  restanteAposCardapio(generoId: number | null): number {
    const genero = this.generoDe(generoId);
    return genero ? this.arredondar(Number(genero.disponivel) - this.totalPlanejado(generoId)) : 0;
  }

  estoqueBaixo(generoId: number | null): boolean {
    const genero = this.generoDe(generoId);
    if (!genero || this.excedeSaldo(generoId) || this.totalPlanejado(generoId) <= 0) {
      return false;
    }
    return this.restanteAposCardapio(generoId) < Number(genero.disponivel) * FRACAO_ESTOQUE_BAIXO;
  }

  private arredondar(valor: number): number {
    return Math.round((valor + Number.EPSILON) * 1000) / 1000;
  }

  // ---- Pedido de reforço ao Diretor (função existente de solicitação de reforço) ----

  get podePedirReforco(): boolean {
    return pode(Recurso.SOLICITACAO_REFORCO, Acao.CADASTRAR);
  }

  abrirReforco(linha: LinhaForm): void {
    const genero = this.generoDe(linha.item_generico);
    if (!genero) {
      return;
    }
    const restante = this.restanteAposCardapio(genero.item_generico_id);
    const refeicao = this.refeicoes.find((opcao) => opcao.valor === this.refeicao)?.label ?? 'cardápio';
    const [ano, mes, dia] = (this.data || '').split('-');
    this.reforco = {
      linha,
      genero,
      opcoes: [],
      carregando: true,
      itemEmpenho: null,
      quantidade: null,
      justificativa: `Estoque baixo de ${genero.descricao} para o ${refeicao.toLowerCase()}`
        + (dia ? ` de ${dia}/${mes}/${ano}` : '')
        + `: restarão ${formatarQuantidade(restante)} ${genero.unidade_medida} após o cardápio.`,
      enviando: false,
      erro: '',
    };

    this.solicitacaoReforcoService.opcoesPorGenero(genero.item_generico_id).subscribe({
      next: (opcoes) => {
        if (!this.reforco) {
          return;
        }
        this.reforco.opcoes = opcoes;
        this.reforco.carregando = false;
        // Sugere o primeiro empenho com saldo na ARP.
        this.reforco.itemEmpenho = opcoes.find((opcao) => this.saldoArp(opcao) >= 1)?.item_empenho ?? null;
      },
      error: () => {
        if (this.reforco) {
          this.reforco.carregando = false;
          this.reforco.erro = 'Não foi possível consultar os empenhos deste gênero.';
        }
      },
    });
  }

  fecharReforco(): void {
    this.reforco = null;
  }

  saldoArp(opcao: OpcaoReforcoGenero): number {
    return Number(opcao.saldo_disponivel_ata) || 0;
  }

  get opcaoReforcoSelecionada(): OpcaoReforcoGenero | undefined {
    return this.reforco?.opcoes.find((opcao) => opcao.item_empenho === this.reforco?.itemEmpenho);
  }

  get pedidoReforcoValido(): boolean {
    const opcao = this.opcaoReforcoSelecionada;
    const quantidade = Number(this.reforco?.quantidade);
    return Boolean(opcao) && !this.reforco!.enviando && quantidade >= 1 && quantidade <= this.saldoArp(opcao!)
      && Boolean(this.reforco!.justificativa.trim());
  }

  enviarReforco(): void {
    const pedido = this.reforco;
    if (!pedido || !this.pedidoReforcoValido) {
      return;
    }
    pedido.enviando = true;
    pedido.erro = '';
    this.solicitacaoReforcoService
      .solicitar(pedido.itemEmpenho!, Number(pedido.quantidade), pedido.justificativa.trim())
      .subscribe({
        next: () => {
          this.feedback.sucesso(`Pedido de reforço de ${pedido.genero.descricao} enviado ao Diretor.`);
          this.reforco = null;
        },
        error: (erro) => {
          pedido.enviando = false;
          pedido.erro = mensagemErroCardapio(erro, 'Não foi possível enviar o pedido de reforço.');
        },
      });
  }

  repetidoNoCardapio(generoId: number | null): boolean {
    if (!generoId) {
      return false;
    }
    return this.secoes
      .flatMap((secao) => secao.linhas)
      .filter((linha) => Number(linha.item_generico) === Number(generoId)).length > 1;
  }

  // ---- Validação ----

  private linhaPreenchida(linha: LinhaForm): boolean {
    return Boolean(linha.item_generico) || Boolean(linha.quantidade) || Boolean(linha.observacao.trim());
  }

  linhaInvalida(linha: LinhaForm): boolean {
    return this.linhaPreenchida(linha) && (!linha.item_generico || !(Number(linha.quantidade) > 0));
  }

  secaoSemTitulo(secao: SecaoForm, indice: number): boolean {
    return indice > 0 && !secao.titulo.trim() && secao.linhas.some((linha) => this.linhaPreenchida(linha));
  }

  /** Não se cria cardápio para um dia que já passou; um rascunho antigo mantém a data que já tinha. */
  get dataNoPassado(): boolean {
    return Boolean(this.data) && this.data < this.hoje() && this.data !== this.dataOriginal;
  }

  get dadosGeraisValidos(): boolean {
    return Boolean(this.refeicao) && Boolean(this.data) && !this.dataNoPassado
      && Number(this.estimativaPessoas) > 0 && Boolean(this.preparacoes.trim());
  }

  get itensPreenchidos(): { secao: string; linha: LinhaForm }[] {
    return this.secoes.flatMap((secao) => secao.linhas
      .filter((linha) => this.linhaPreenchida(linha))
      .map((linha) => ({ secao: secao.titulo.trim(), linha })));
  }

  get detalhamentoValido(): boolean {
    return this.secoes.every((secao, indice) =>
      !this.secaoSemTitulo(secao, indice) && secao.linhas.every((linha) => !this.linhaInvalida(linha)),
    );
  }

  get generosSemSaldo(): DisponibilidadeGenero[] {
    const ids = [...new Set(this.itensPreenchidos.map(({ linha }) => Number(linha.item_generico)))];
    return ids
      .filter((id) => this.excedeSaldo(id) || this.generoSemSaldo(id))
      .map((id) => this.generoDe(id)!);
  }

  /** O cardápio só existe com gêneros do estoque, todos dentro do saldo disponível. */
  get podeSalvar(): boolean {
    return !this.salvando && !this.semEstoque && this.dadosGeraisValidos && this.detalhamentoValido
      && this.itensPreenchidos.length > 0 && this.generosSemSaldo.length === 0;
  }

  get podeEnviar(): boolean {
    return this.podeSalvar;
  }

  // ---- Gravação ----

  private montarCardapio(): CardapioInsert {
    const itens: ItemCardapio[] = this.itensPreenchidos.map(({ secao, linha }, ordem) => ({
      ordem,
      secao,
      item_generico: Number(linha.item_generico),
      quantidade_planejada: Number(linha.quantidade),
      observacao: linha.observacao.trim(),
    }));
    return {
      refeicao: this.refeicao,
      data: this.data,
      estimativa_pessoas: Number(this.estimativaPessoas),
      preparacoes: this.preparacoes,
      observacoes: this.observacoes.trim(),
      itens,
    };
  }

  salvarRascunho(): void {
    this.formSubmitted = true;
    if (!this.podeSalvar) {
      return;
    }
    this.gravar((cardapio) => {
      this.feedback.sucesso('Rascunho do cardápio salvo.');
      this.abrirCardapio(cardapio.id);
    });
  }

  // ---- Revisão antes do envio ----

  revisar(): void {
    this.formSubmitted = true;
    this.reforco = null;
    if (!this.podeEnviar) {
      return;
    }

    this.previa = this.montarPrevia();
    this.impactoEstoque = this.calcularImpacto();
    this.erro = '';
    this.emRevisao = true;
    window.scrollTo({ top: 0 });
    setTimeout(() => this.tituloRevisao?.nativeElement.focus());
  }

  voltarParaEdicao(): void {
    if (this.salvando) {
      return;
    }
    this.emRevisao = false;
    this.erro = '';
  }

  get refeicaoDescricao(): string {
    return this.refeicoes.find((opcao) => opcao.valor === this.refeicao)?.label ?? '';
  }

  get dataLocal(): Date {
    const [ano, mes, dia] = this.data.split('-').map(Number);
    return new Date(ano, mes - 1, dia);
  }

  get totalGenerosRevisao(): number {
    return this.impactoEstoque.length;
  }

  get generosComEstoqueBaixo(): number {
    return this.impactoEstoque.filter((impacto) => impacto.estoqueBaixo).length;
  }

  /** O documento da revisão usa o mesmo componente do documento impresso. */
  private montarPrevia(): Cardapio {
    const dados = this.montarCardapio();
    return {
      id: this.id ?? 0,
      refeicao: dados.refeicao as Cardapio['refeicao'],
      refeicao_descricao: this.refeicaoDescricao,
      data: dados.data,
      estimativa_pessoas: Number(dados.estimativa_pessoas),
      preparacoes: dados.preparacoes,
      observacoes: dados.observacoes,
      status: 'RASCUNHO',
      status_descricao: 'Rascunho',
      motivo_recusa: '',
      motivo_alteracao: '',
      criado_por_nome: this.nomeNutricionista,
      criado_em: '',
      atualizado_em: '',
      enviado_em: null,
      aprovado_por_nome: null,
      aprovado_em: null,
      consumo_informado_em: null,
      finalizado_por_nome: null,
      finalizado_em: null,
      substituido_por: null,
      substitui: null,
      itens: dados.itens.map((item, indice) => {
        const genero = this.generoDe(item.item_generico);
        return {
          ...item,
          id: -(indice + 1),
          descricao: genero?.descricao,
          catmat: genero?.catmat,
          unidade_medida: genero?.unidade_medida,
          conteudo_embalagem: genero?.conteudo_embalagem,
          unidade_embalagem: genero?.unidade_embalagem,
          quantidade_liberada: null,
          quantidade_consumida: null,
        };
      }),
    };
  }

  private calcularImpacto(): ImpactoEstoque[] {
    const ids = [...new Set(this.itensPreenchidos.map(({ linha }) => Number(linha.item_generico)))];
    return ids.map((id) => ({
      genero: this.generoDe(id)!,
      quantidade: this.arredondar(this.totalPlanejado(id)),
      restante: this.restanteAposCardapio(id),
      estoqueBaixo: this.estoqueBaixo(id),
    }));
  }

  /** Salva o cardápio e o envia ao estoque; só é chamado a partir da revisão. */
  confirmarEnvio(): void {
    if (!this.emRevisao || !this.podeEnviar) {
      return;
    }

    this.gravar((cardapio) => {
      this.salvando = true;
      this.cardapioService.enviar(cardapio.id).subscribe({
        next: () => {
          this.salvando = false;
          this.feedback.sucesso('Cardápio enviado. O estoque foi notificado para aprovar a retirada.');
          this.abrirCardapio(cardapio.id);
        },
        error: (erro) => {
          this.salvando = false;
          // O rascunho já está gravado: volta à edição do mesmo cardápio para ajustar.
          this.id = cardapio.id;
          this.emRevisao = false;
          this.erro = mensagemErroCardapio(erro, 'O rascunho foi salvo, mas não foi possível enviá-lo.');
          this.carregarDisponibilidade();
        },
      });
    });
  }

  private gravar(depois: (cardapio: Cardapio) => void): void {
    this.salvando = true;
    this.erro = '';
    const requisicao: Observable<Cardapio> = this.cardapioService.salvar(this.montarCardapio(), this.id ?? undefined);
    requisicao.subscribe({
      next: (cardapio) => {
        this.salvando = false;
        this.id = cardapio.id;
        depois(cardapio);
      },
      error: (erro) => {
        this.salvando = false;
        this.erro = mensagemErroCardapio(erro, 'Não foi possível salvar o cardápio. Revise os campos.');
      },
    });
  }

  private abrirCardapio(id: number): void {
    this.router.navigate(['/cardapio'], { queryParams: { id } });
  }
}
