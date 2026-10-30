import { DatePipe } from '@angular/common';
import { Component, HostListener, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Title } from '@angular/platform-browser';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Observable } from 'rxjs';

import { Cardapio, DisponibilidadeGenero, ItemCardapio } from '../../../model/cardapio';
import { Acao, pode, Recurso } from '../../../security/rbac';
import { CardapioService, mensagemErroCardapio } from '../../../service/cardapio.service';
import { FeedbackService } from '../../../service/feedback.service';
import { BotaoVoltar } from '../../utils/botao-voltar/botao-voltar';
import { EstadoConteudo } from '../../utils/estado-conteudo/estado-conteudo';
import { CardapioDocumento } from '../cardapio-documento/cardapio-documento';
import {
  agruparPorSecao,
  classeStatusCardapio,
  formatarQuantidade,
  nomeArquivoCardapio,
  unidadeComEmbalagem,
} from '../cardapio-util';

type MotivoAcao = 'recusar' | 'devolver' | 'alterar' | 'recusarAlteracao' | null;

@Component({
  selector: 'app-cardapio-detalhe',
  imports: [BotaoVoltar, CardapioDocumento, DatePipe, EstadoConteudo, FormsModule, RouterLink],
  templateUrl: './cardapio-detalhe.html',
  styleUrl: './cardapio-detalhe.scss',
})
export class CardapioDetalhe implements OnInit {
  readonly classeStatus = classeStatusCardapio;
  readonly formatarQuantidade = formatarQuantidade;
  readonly unidadeComEmbalagem = unidadeComEmbalagem;

  cardapio: Cardapio | null = null;
  grupos: { secao: string; itens: ItemCardapio[] }[] = [];
  carregando = true;
  erroCarregamento = '';

  /** Quantidade em edição por item: liberada (aprovação) ou consumida (consumo real). */
  quantidades: Record<number, number | null> = {};
  saldos = new Map<number, DisponibilidadeGenero>();
  motivoAcao: MotivoAcao = null;
  motivo = '';
  processando = false;
  erroAcao = '';

  constructor(
    private cardapioService: CardapioService,
    private feedback: FeedbackService,
    private route: ActivatedRoute,
    private router: Router,
    private title: Title,
  ) {}

  private tituloAntesDaImpressao: string | null = null;

  /** O navegador usa o título da página como nome do PDF: "jantar-14-10-2026". */
  @HostListener('window:beforeprint')
  aoIniciarImpressao(): void {
    if (!this.cardapio) {
      return;
    }
    this.tituloAntesDaImpressao = this.title.getTitle();
    this.title.setTitle(nomeArquivoCardapio(this.cardapio));
  }

  @HostListener('window:afterprint')
  aoTerminarImpressao(): void {
    if (this.tituloAntesDaImpressao !== null) {
      this.title.setTitle(this.tituloAntesDaImpressao);
      this.tituloAntesDaImpressao = null;
    }
  }

  ngOnInit(): void {
    // Acompanha o parâmetro: os links entre o cardápio substituído e o novo rascunho reaproveitam a página.
    this.route.queryParamMap.subscribe((params) => {
      const id = Number(params.get('id'));
      if (!Number.isInteger(id) || id <= 0) {
        this.carregando = false;
        this.erroCarregamento = 'Não foi possível identificar o cardápio.';
        return;
      }
      this.erroCarregamento = '';
      this.carregar(id);
    });
  }

  carregar(id: number): void {
    this.carregando = true;
    this.cardapioService.obter(id).subscribe({
      next: (cardapio) => this.aplicar(cardapio),
      error: () => {
        this.carregando = false;
        this.erroCarregamento = 'Não foi possível carregar o cardápio.';
      },
    });
  }

  private aplicar(cardapio: Cardapio): void {
    this.cardapio = cardapio;
    this.grupos = agruparPorSecao(cardapio.itens);
    this.carregando = false;
    this.motivoAcao = null;
    this.motivo = '';
    this.erroAcao = '';
    this.prepararQuantidades();

    if (this.modoAprovacao) {
      // O limite da retirada considera o saldo utilizável na data planejada do cardápio.
      this.cardapioService.disponibilidade(cardapio.id, cardapio.data).subscribe({
        next: (dados) => {
          this.saldos = new Map(dados.map((item) => [item.item_generico_id, item]));
          this.prepararQuantidades();
        },
      });
    }
  }

  private prepararQuantidades(): void {
    if (!this.cardapio) {
      return;
    }
    this.quantidades = {};
    for (const item of this.cardapio.itens) {
      if (this.modoAprovacao) {
        const saldo = this.saldoAtual(item);
        const planejada = Number(item.quantidade_planejada);
        this.quantidades[item.id!] = saldo === null ? planejada : Math.min(planejada, saldo);
      } else if (this.modoConsumo) {
        this.quantidades[item.id!] = Number(item.quantidade_consumida ?? item.quantidade_liberada ?? 0);
      }
    }
  }

  // ---- Papéis e etapas ----

  get podeEditar(): boolean {
    return pode(Recurso.CARDAPIO, Acao.EDITAR);
  }

  get podeAprovar(): boolean {
    return pode(Recurso.CARDAPIO, Acao.APROVAR);
  }

  get editavel(): boolean {
    return this.podeEditar && ['RASCUNHO', 'RECUSADO'].includes(this.cardapio?.status ?? '');
  }

  get modoAprovacao(): boolean {
    return this.podeAprovar && this.cardapio?.status === 'ENVIADO';
  }

  get modoConsumo(): boolean {
    return this.podeEditar && this.cardapio?.status === 'APROVADO';
  }

  get podeCancelarEnvio(): boolean {
    return this.podeEditar && this.cardapio?.status === 'ENVIADO';
  }

  /** Estoquista decide sobre o pedido de alteração de um cardápio já aprovado. */
  get modoAlteracao(): boolean {
    return this.podeAprovar && this.cardapio?.status === 'ALTERACAO_SOLICITADA';
  }

  get modoConfirmacao(): boolean {
    return this.podeAprovar && this.cardapio?.status === 'CONSUMO_INFORMADO';
  }

  get mostrarLiberada(): boolean {
    return this.modoAprovacao || this.cardapio?.itens.some((item) => item.quantidade_liberada !== null) === true;
  }

  get mostrarConsumida(): boolean {
    return this.modoConsumo || this.cardapio?.itens.some((item) => item.quantidade_consumida !== null) === true;
  }

  get mostrarAcerto(): boolean {
    return ['CONSUMO_INFORMADO', 'FINALIZADO'].includes(this.cardapio?.status ?? '');
  }

  // ---- Cálculos ----

  saldoAtual(item: ItemCardapio): number | null {
    const saldo = this.saldos.get(item.item_generico);
    return saldo ? Number(saldo.disponivel) : null;
  }

  /** Soma do que está sendo liberado para o mesmo gênero (ele pode aparecer em mais de uma linha). */
  private totalLiberadoDoGenero(item: ItemCardapio): number {
    return (this.cardapio?.itens ?? [])
      .filter((outro) => outro.item_generico === item.item_generico)
      .reduce((total, outro) => total + (Number(this.quantidades[outro.id!]) || 0), 0);
  }

  erroLiberada(item: ItemCardapio): string {
    const valor = this.quantidades[item.id!];
    if (valor === null || valor === undefined || Number(valor) < 0) {
      return 'Informe uma quantidade (0 para não liberar).';
    }
    if (Number(valor) > Number(item.quantidade_planejada)) {
      return 'Não pode ser maior que o planejado.';
    }
    const saldo = this.saldoAtual(item);
    if (saldo !== null && this.totalLiberadoDoGenero(item) > saldo + 0.0005) {
      return `Saldo disponível: ${formatarQuantidade(saldo)} ${item.unidade_medida}.`;
    }
    return '';
  }

  erroConsumo(item: ItemCardapio): string {
    const valor = this.quantidades[item.id!];
    return valor === null || valor === undefined || Number(valor) < 0 ? 'Informe quanto foi usado (0 se não usou).' : '';
  }

  get aprovacaoValida(): boolean {
    return (this.cardapio?.itens ?? []).every((item) => !this.erroLiberada(item));
  }

  get consumoValido(): boolean {
    return (this.cardapio?.itens ?? []).every((item) => !this.erroConsumo(item));
  }

  ajustada(item: ItemCardapio): boolean {
    return Number(this.quantidades[item.id!]) !== Number(item.quantidade_planejada);
  }

  /** Consumido menos liberado: positivo = retirar mais; negativo = devolver sobra. */
  diferenca(item: ItemCardapio): number {
    return Number(item.quantidade_consumida ?? 0) - Number(item.quantidade_liberada ?? 0);
  }

  textoAcerto(item: ItemCardapio): string {
    const diferenca = this.diferenca(item);
    const unidade = item.unidade_medida;
    const finalizado = this.cardapio?.status === 'FINALIZADO';
    if (Math.abs(diferenca) < 0.0005) {
      return 'Sem diferença';
    }
    if (diferenca < 0) {
      return `${finalizado ? 'Devolvido' : 'Devolver'} ${formatarQuantidade(-diferenca)} ${unidade} ao estoque`;
    }
    return `${finalizado ? 'Retirado' : 'Retirar'} mais ${formatarQuantidade(diferenca)} ${unidade}`;
  }

  private itensComQuantidade() {
    return (this.cardapio?.itens ?? []).map((item) => ({ item: item.id!, quantidade: Number(this.quantidades[item.id!]) }));
  }

  // ---- Ações ----

  private executar(requisicao: Observable<Cardapio>, sucesso: string, erroPadrao: string): void {
    this.processando = true;
    this.erroAcao = '';
    requisicao.subscribe({
      next: (cardapio) => {
        this.processando = false;
        this.feedback.sucesso(sucesso);
        this.aplicar(cardapio);
      },
      error: (erro) => {
        this.processando = false;
        this.erroAcao = mensagemErroCardapio(erro, erroPadrao);
      },
    });
  }

  editar(): void {
    this.router.navigate(['/cardapios/editar'], { queryParams: { id: this.cardapio!.id } });
  }

  enviar(): void {
    this.feedback.confirmar({
      titulo: 'Enviar cardápio ao estoque?',
      mensagem: 'Os gêneros ficarão reservados até o Estoquista aprovar ou recusar a retirada.',
      textoConfirmar: 'Enviar',
    }).then((ok) => ok && this.executar(
      this.cardapioService.enviar(this.cardapio!.id),
      'Cardápio enviado. O estoque foi notificado.',
      'Não foi possível enviar o cardápio.',
    ));
  }

  cancelarEnvio(): void {
    this.feedback.confirmar({
      titulo: 'Cancelar o envio?',
      mensagem: 'O cardápio sai da fila do estoque e volta a ser rascunho para você alterar e reenviar.',
      textoConfirmar: 'Cancelar envio',
    }).then((ok) => ok && this.executar(
      this.cardapioService.cancelarEnvio(this.cardapio!.id),
      'Envio cancelado. O cardápio voltou a ser rascunho.',
      'Não foi possível cancelar o envio.',
    ));
  }

  aceitarAlteracao(): void {
    this.feedback.confirmar({
      titulo: 'Aceitar a alteração?',
      mensagem: 'Tudo o que foi liberado volta ao estoque agora. A nutricionista recebe um novo rascunho '
        + 'para ajustar e reenviar, que passará de novo pela sua aprovação.',
      textoConfirmar: 'Aceitar',
    }).then((ok) => {
      if (!ok) {
        return;
      }
      const original = this.cardapio!.id;
      this.processando = true;
      this.erroAcao = '';
      // A resposta é o novo rascunho; o Estoquista continua vendo o original, agora substituído.
      this.cardapioService.aceitarAlteracao(original).subscribe({
        next: () => {
          this.processando = false;
          this.feedback.sucesso('Alteração aceita. Os gêneros voltaram ao estoque e a nutricionista foi notificada.');
          this.carregar(original);
        },
        error: (erro) => {
          this.processando = false;
          this.erroAcao = mensagemErroCardapio(erro, 'Não foi possível aceitar a alteração.');
        },
      });
    });
  }

  excluir(): void {
    this.feedback.confirmar({
      titulo: 'Excluir cardápio?',
      mensagem: 'O rascunho será removido permanentemente.',
      textoConfirmar: 'Excluir',
      destrutiva: true,
    }).then((ok) => {
      if (!ok) {
        return;
      }
      this.processando = true;
      this.cardapioService.excluir(this.cardapio!.id).subscribe({
        next: () => {
          this.feedback.sucesso('Cardápio excluído.');
          this.router.navigate(['/cardapios']);
        },
        error: (erro) => {
          this.processando = false;
          this.erroAcao = mensagemErroCardapio(erro, 'Não foi possível excluir o cardápio.');
        },
      });
    });
  }

  aprovar(): void {
    if (!this.aprovacaoValida) {
      return;
    }
    const ajustes = (this.cardapio?.itens ?? []).filter((item) => this.ajustada(item)).length;
    this.feedback.confirmar({
      titulo: 'Aprovar a retirada?',
      mensagem: (ajustes ? `${ajustes} item(ns) terão a quantidade ajustada. ` : '')
        + 'As quantidades liberadas sairão do estoque agora.',
      textoConfirmar: 'Aprovar',
    }).then((ok) => ok && this.executar(
      this.cardapioService.aprovar(this.cardapio!.id, this.itensComQuantidade()),
      'Retirada aprovada e registrada no estoque.',
      'Não foi possível aprovar a retirada.',
    ));
  }

  informarConsumo(): void {
    if (!this.consumoValido) {
      return;
    }
    this.feedback.confirmar({
      titulo: 'Enviar o consumo real?',
      mensagem: 'O Estoquista vai conferir e confirmar a devolução das sobras e a retirada do que foi usado a mais.',
      textoConfirmar: 'Enviar',
    }).then((ok) => ok && this.executar(
      this.cardapioService.informarConsumo(this.cardapio!.id, this.itensComQuantidade()),
      'Consumo real enviado para conferência do estoque.',
      'Não foi possível registrar o consumo.',
    ));
  }

  confirmarConsumo(): void {
    this.feedback.confirmar({
      titulo: 'Confirmar o acerto do estoque?',
      mensagem: 'As sobras voltarão ao estoque e o que foi usado a mais será retirado.',
      textoConfirmar: 'Confirmar',
    }).then((ok) => ok && this.executar(
      this.cardapioService.confirmarConsumo(this.cardapio!.id),
      'Acerto do estoque concluído. Cardápio finalizado.',
      'Não foi possível confirmar o consumo.',
    ));
  }

  abrirMotivo(acao: MotivoAcao): void {
    this.motivoAcao = acao;
    this.motivo = '';
    this.erroAcao = '';
  }

  enviarMotivo(): void {
    const motivo = this.motivo.trim();
    if (!motivo || !this.cardapio) {
      return;
    }
    if (this.motivoAcao === 'recusar') {
      this.executar(
        this.cardapioService.recusar(this.cardapio.id, motivo),
        'Cardápio recusado. A nutricionista foi notificada.',
        'Não foi possível recusar o cardápio.',
      );
    } else if (this.motivoAcao === 'devolver') {
      this.executar(
        this.cardapioService.devolverConsumo(this.cardapio.id, motivo),
        'Consumo devolvido para correção.',
        'Não foi possível devolver o consumo.',
      );
    } else if (this.motivoAcao === 'alterar') {
      this.executar(
        this.cardapioService.solicitarAlteracao(this.cardapio.id, motivo),
        'Pedido de alteração enviado. O estoque foi notificado.',
        'Não foi possível solicitar a alteração.',
      );
    } else if (this.motivoAcao === 'recusarAlteracao') {
      this.executar(
        this.cardapioService.recusarAlteracao(this.cardapio.id, motivo),
        'Alteração recusada. A nutricionista foi notificada.',
        'Não foi possível recusar a alteração.',
      );
    }
  }

  get rotuloMotivo(): string {
    switch (this.motivoAcao) {
      case 'recusar':
        return 'Motivo da recusa *';
      case 'devolver':
        return 'O que precisa ser corrigido no consumo? *';
      case 'alterar':
        return 'O que precisa mudar no cardápio? *';
      default:
        return 'Por que a alteração não pode ser feita? *';
    }
  }

  get destinatarioMotivo(): string {
    return this.motivoAcao === 'alterar' ? 'O Estoquista verá esta mensagem.' : 'A nutricionista verá esta mensagem.';
  }

  imprimir(): void {
    window.print();
  }
}
