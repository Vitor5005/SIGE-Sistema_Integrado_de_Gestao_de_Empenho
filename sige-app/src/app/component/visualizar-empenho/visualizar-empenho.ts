import { Component, ElementRef, ViewChild } from '@angular/core';
import { ActivatedRoute, Router, RouterLink, TitleStrategy } from '@angular/router';
import { BotaoVoltar } from '../utils/botao-voltar/botao-voltar';
import { CommonModule } from '@angular/common';
import { EmpenhoService } from '../../service/empenho.service';
import { Empenho } from '../../model/empenho';
import { ItemEmpenho } from '../../model/itemEmpenho';
import { OperacaoItem } from '../../model/operacao_item';
import { OperacaoItemService } from '../../service/operacao-item.service';
import { OperacaoItemInsert } from '../../model/operacao_item_insert';
import { FormsModule } from '@angular/forms';
import { AtaService } from '../../service/ata.service';
import { ItemAtaService } from '../../service/item-ata.service';
import { ItemEmpenhoService } from '../../service/item-empenho.service';
import { ItemOrdemInsert } from '../../model/itemOrdem_insert';
import { OrdemEntregaInsert } from '../../model/ordem_entrega_insert';
import { ItemOrdemService } from '../../service/item-ordem.service';
import { OrdemEntregaService } from '../../service/ordem-entrega.service';
import { forkJoin, switchMap } from 'rxjs';
import { ItemOrdem } from '../../model/itemOrdem';

@Component({
  selector: 'app-visualizar-empenho',
  imports: [BotaoVoltar, CommonModule, FormsModule],
  templateUrl: './visualizar-empenho.html',
  styleUrl: './visualizar-empenho.scss',
})
export class VisualizarEmpenho {
  tipo: 'reforco' | 'anulacao' = 'reforco';
  isSolicitandoEntrega: boolean = false;
  private permitirFecharModalSemConfirmacao: boolean = false;
  constructor(
    private router: Router,
    private empenhoService: EmpenhoService,
    private operacaoItemService: OperacaoItemService,
    private ataService: AtaService,
    private itemAtaService: ItemAtaService,
    private itemEmpenhoService: ItemEmpenhoService,
    private ordemEntregaService: OrdemEntregaService,
    private itemOrdemService: ItemOrdemService,
    private route: ActivatedRoute
  ) { }

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

  get podeSolicitarEntrega(): boolean {
    return (
      !this.isSolicitandoEntrega &&
      this.possuiItensSelecionados &&
      this.dataPrevisaoPreenchida &&
      this.arquivoPreenchido &&
      this.itensSelecionadosComQuantidadeValida
    );
  }

  get todayDate(): string {
    return new Date().toISOString().split('T')[0];
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

  enviarPara(rota: string, id?: number) {
    if (id) {
      this.router.navigate([rota], { queryParams: { id } });
    }
    else {
      this.router.navigate([rota]);
    }
  }
  prepararOperacao(tipoOperacao: 'reforco' | 'anulacao') {
    this.tipo = tipoOperacao;
  }


  ngOnInit() {
    const id = this.route.snapshot.queryParams['id'];

    if (id) {
      this.getEmpenho(Number(id));
      this.getItensEmpenho(Number(id));
      this.getOperacoesEmpenho(Number(id));
    }
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
        const desejaSair = confirm('Você já preencheu dados da solicitação. Se sair agora, perderá toda a operação. Deseja sair mesmo assim?');
        if (!desejaSair) {
          event.preventDefault();
        }
      }
    });

  }

  getEmpenho(id: number): void {
    this.empenhoService.getById(id).subscribe({
      next: (resposta: Empenho) => {
        this.empenho = resposta;
      }
    });
  }

  getItensEmpenho(id: number): void {
    this.empenhoService.itensDoEmpenho(id).subscribe({
      next: (resposta: ItemEmpenho[]) => {
        this.itensEmpenho = resposta;
      },
      complete: () => {
        this.itemEmpenhoModal = this.itensEmpenho[0];
        this.itensEmpenho.forEach(item => {
          let itemOrdemInsert = <ItemOrdemInsert>{};
          itemOrdemInsert.item_empenho = item.id;
          itemOrdemInsert.observacao = "";
          itemOrdemInsert.quantidade_entregue = 0;
          this.itensOrdemInsert.push(itemOrdemInsert);
        });
        this.itensSelecionados = new Array(this.itensEmpenho.length).fill(false);
      }
    });
  }

  getOperacoesEmpenho(id: number): void {
    this.empenhoService.operacaoDoEmpenho(id).subscribe({
      next: (resposta: OperacaoItem[]) => {
        this.operacoesEmpenho = resposta;
      }
    });
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

  carregarItemEmpenho(item: ItemEmpenho) {
    this.itemEmpenhoModal = item;
    this.operacaoItem_insercao.item_empenho = item.id;
  }

  trocarOperacao(tipo: string): void {
    this.operacaoItem_insercao.tipo = tipo;
  }

  reiniciarModalSolicitacao(): void {
    if (this.isSolicitandoEntrega) {
      return;
    }

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

  salvarOperacaoItem(): void {
    this.operacaoItem_insercao.data = new Date();
    this.operacaoItemService.save(this.operacaoItem_insercao).subscribe({
      complete: () => {
        this.atualizarItemEmpenho(this.operacaoItem_insercao.valor, this.operacaoItem_insercao.tipo, this.operacaoItem_insercao.item_empenho);
      }
    });
  }

  atualizarItemEmpenho(valor: number, operacao: string, item_id: number): void {
    const qtdAtual = Number(this.itemEmpenhoModal.quantidade_atual) || 0;
    const delta = Number(valor) || 0;

    let novaQuantidade = qtdAtual;

    if (operacao === 'ref') {
      novaQuantidade = qtdAtual + delta;
    } else if (operacao === 'anl') {
      novaQuantidade = qtdAtual - delta;
    }

    novaQuantidade = Math.round((novaQuantidade + Number.EPSILON) * 100) / 100;

    this.itemEmpenhoService.patch(item_id, { quantidade_atual: novaQuantidade }).subscribe({
      complete: () => {
        this.atualizarEmpenho(valor * this.itemEmpenhoModal.item_ata.valor_unitario, operacao, this.empenho.id);
      }
    });
  }

  atualizarEmpenho(valor: number, operacao: string, item_id: number): void {
    const qtdAtual = Number(this.empenho.valor_total) || 0;
    const delta = Number(valor) || 0;

    let novaQuantidade = qtdAtual;

    if (operacao === 'ref') {
      novaQuantidade = qtdAtual + delta;
    } else if (operacao === 'anl') {
      novaQuantidade = qtdAtual - delta;
    }

    novaQuantidade = Math.round((novaQuantidade + Number.EPSILON) * 100) / 100;

    this.empenhoService.patch(item_id, { valor_total: novaQuantidade }).subscribe({
      complete: () => {
        window.location.reload();
      }
    });
  }

  solicitarEntrega() {
    if (this.isSolicitandoEntrega) {
      return;
    }

    if (!this.podeSolicitarEntrega) {
      alert('Preencha data de previsão, anexo e quantidade válida de todos os itens selecionados.');
      return;
    }

    this.isSolicitandoEntrega = true;

    this.ordemEntregaInsert.codigo = this.gerarCodigoPedidoEntrega();
    this.ordemEntregaInsert.empenho = this.empenho.id;
    this.ordemEntregaInsert.data_emissao = new Date();
    this.ordemEntregaInsert.status = 'esp';
    this.ordemEntregaInsert.valor_total_executado = this.calcularSomaTotalItensSolicitados();

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
          }
        });
      },
      error: (err) => {
        this.isSolicitandoEntrega = false;
        console.error('Erro ao criar ordem de entrega', err);
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
      complete: () => {
        alert('Pedido de entrega solicitado com sucesso!');
        window.location.reload();
      },
      error: (err) => {
        this.isSolicitandoEntrega = false;
        console.error('Erro ao enviar e-mail do pedido', err);
      }
    });
  }

  tentarFecharModalSolicitacao(): void {
    if (this.isSolicitandoEntrega) {
      return;
    }

    if (this.possuiDadosPreenchidosModal) {
      const desejaSair = confirm('Você já preencheu dados da solicitação. Se sair agora, perderá toda a operação. Deseja sair mesmo assim?');
      if (!desejaSair) {
        return;
      }
    }

    if (this.fecharModalInternoBtn?.nativeElement) {
      this.permitirFecharModalSemConfirmacao = true;
      this.fecharModalInternoBtn.nativeElement.click();
    }
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
