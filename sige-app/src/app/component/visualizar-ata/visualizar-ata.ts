import { BotaoVoltar } from './../utils/botao-voltar/botao-voltar';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { AtaService } from '../../service/ata.service';
import { Ata } from '../../model/ata';
import { DecimalPipe, KeyValuePipe } from '@angular/common';
import { Empenho } from '../../model/empenho';
import { ItemAta } from '../../model/itemAta';
import { ItemEmpenho } from '../../model/itemEmpenho';
import { FormsModule } from '@angular/forms';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Paginacao } from '../utils/paginacao/paginacao';
import { ItemGenericoService } from '../../service/item-generico.service';
import { ItemGenerico } from '../../model/item_generico';
import { ItemAtaService } from '../../service/item-ata.service';
import { ItemEmpenhoService } from '../../service/item-empenho.service';
import { ItemAtaInsert } from '../../model/itemAta_insert';
import { ItemEmpenhoInsert } from '../../model/itemEmpenho_insert';
import { OperacaoItemService } from '../../service/operacao-item.service';
import { OperacaoItemInsert } from '../../model/operacao_item_insert';
import { FeedbackService } from '../../service/feedback.service';
import { EstadoConteudo } from '../utils/estado-conteudo/estado-conteudo';
import { Acao, pode, Recurso } from '../../security/rbac';

@Component({
  selector: 'app-visualizar-ata',
  standalone: true,
  imports: [DecimalPipe, BotaoVoltar, FormsModule, BarraPesquisa, KeyValuePipe, Paginacao, RouterLink, EstadoConteudo],
  templateUrl: './visualizar-ata.html',
  styleUrl: './visualizar-ata.scss',
})
export class VisualizarAta {
  readonly pode = pode;
  readonly Acao = Acao;
  readonly Recurso = Recurso;

  constructor(
    private router: Router,
    private ataService: AtaService,
    private route: ActivatedRoute,
    private itemGenericoService: ItemGenericoService,
    private itemAtaService: ItemAtaService,
    private itemEmpenhoService: ItemEmpenhoService,
    private operacaService: OperacaoItemService,
    private feedback: FeedbackService
  ) { }

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild('myInput') input!: ElementRef;
  @ViewChild('fecharModalInternoBtn') fecharModalInternoBtn!: ElementRef<HTMLButtonElement>;

  ata: Ata = <Ata>{};
  empenho: Empenho = <Empenho>{};
  itens: Array<ItemEmpenho> = [];
  isLoadingPage: boolean = true;
  errorMessagePage: string = '';
  idPagina: number | null = null;
  isLoadingEmpenho: boolean = false;
  errorMessageEmpenho: string = '';
  isLoadingItens: boolean = false;
  errorMessageItens: string = '';
  validade: string = '';
  itemGenerico: Array<ItemGenerico> = [];
  itemGenericoCadastrados: Array<number> = [];
  currentPageItemGenerico: number = 1;
  pageSizeItemGenerico: number = 5;
  termoBuscaItemGenerico: string = '';
  isLoadingItemGenerico: boolean = false;
  errorMessageItemGenerico: string = '';
  operacaoInsercao = <OperacaoItemInsert>{};

  modal_page: number = 0;
  jump_page: boolean = false;
  formSubmittedPage1: boolean = false;
  formSubmittedPage2: boolean = false;
  isSaving: boolean = false;
  errorMessageModal: string = '';
  private permitirFecharModalSemConfirmacao: boolean = false;

  itemGenerico_insercao: ItemGenerico = <ItemGenerico>{
    unidade_medida: '',
    categoria: ''
  };
  itemAta_insercao: ItemAtaInsert = <ItemAtaInsert>{
    quantidade_licitada: 0,
    valor_unitario: 0,
  };
  itemEmpenho_insercao: ItemEmpenhoInsert = <ItemEmpenhoInsert>{};

  unidade_medida = {
    KG: 'Quilograma(KG)',
    G: 'Grama(G)',
    L: 'Litro(L)',
    mL: 'Mililitro(mL)',
    duzia: 'Duzia',
    cento: 'Cento',
    PCT: 'Pacote(PCT)',
    CX: 'Caixa(CX)',
    FND: 'Fardo(FND)',
    GAR: 'Garrafa(GAR)',
    lata: 'Lata',
    un: 'Unidade(UN)'
  };

  categoria = {
    tempS: 'Tempero Secos',
    SM: 'Secos / Mercearia',
    Lac: 'Lácteos e Derivados',
    Oli: 'Óleos, Azeites e Vinagres',
    MolCo: 'Molhos e Condimentos',
    Fr: 'Frutas',
    Le: 'Legumes',
    Pr: 'Proteínas'
  };

  get catmatValido(): boolean {
    const catmat = (this.itemGenerico_insercao.catmat || '').trim();
    return /^\d{6}$/.test(catmat);
  }

  get descricaoValida(): boolean {
    const descricao = (this.itemGenerico_insercao.descricao || '').trim();
    return descricao.length > 0 && descricao.length <= 300;
  }

  get unidadeMedidaValida(): boolean {
    return Boolean(this.itemGenerico_insercao.unidade_medida?.trim());
  }

  get categoriaValida(): boolean {
    return Boolean(this.itemGenerico_insercao.categoria?.trim());
  }

  get itemGenericoFormValido(): boolean {
    return this.catmatValido && this.descricaoValida && this.unidadeMedidaValida && this.categoriaValida;
  }

  get quantidadeLicitadaValida(): boolean {
    const quantidade = Number(this.itemAta_insercao.quantidade_licitada) || 0;
    return quantidade > 0;
  }

  get valorUnitarioValido(): boolean {
    const valor = Number(this.itemAta_insercao.valor_unitario) || 0;
    return valor > 0;
  }

  get marcaValida(): boolean {
    const marca = (this.itemAta_insercao.marca || '').trim();
    return marca.length > 0 && marca.length <= 255;
  }

  get itemAtaFormValido(): boolean {
    return this.quantidadeLicitadaValida && this.valorUnitarioValido && this.marcaValida;
  }

  get podeConcluirCadastroItem(): boolean {
    return !this.isSaving && this.itemAtaFormValido && (this.jump_page || this.itemGenericoFormValido);
  }

  get itensGenericosPaginados(): ItemGenerico[] {
    const inicio = (this.currentPageItemGenerico - 1) * this.pageSizeItemGenerico;
    return this.itemGenerico.slice(inicio, inicio + this.pageSizeItemGenerico);
  }

  get totalItensGenericosDisponiveis(): number {
    return this.itemGenerico.length;
  }

  get possuiEmpenhoRelacionado(): boolean {
    return Boolean(this.empenho?.id);
  }

  get possuiDadosModalPreenchidos(): boolean {
    return Boolean(
      this.itemGenerico_insercao.catmat ||
      this.itemGenerico_insercao.descricao ||
      this.itemGenerico_insercao.unidade_medida ||
      this.itemGenerico_insercao.categoria ||
      this.itemAta_insercao.quantidade_licitada ||
      this.itemAta_insercao.valor_unitario ||
      this.itemAta_insercao.marca
    );
  }

  arredondarDuasCasas(valor: number): number {
    return Math.round((valor + Number.EPSILON) * 100) / 100;
  }

  onCatmatInput(): void {
    this.itemGenerico_insercao.catmat = (this.itemGenerico_insercao.catmat || '')
      .replace(/\D/g, '')
      .slice(0, 6);
  }

  onDescricaoInput(): void {
    this.itemGenerico_insercao.descricao = (this.itemGenerico_insercao.descricao || '').slice(0, 300);
  }

  onMarcaInput(): void {
    this.itemAta_insercao.marca = (this.itemAta_insercao.marca || '').slice(0, 255);
  }

  validarQuantidadeLicitada(): void {
    const valorAtual = this.arredondarDuasCasas(Number(this.itemAta_insercao.quantidade_licitada) || 0);
    this.itemAta_insercao.quantidade_licitada = valorAtual < 0 ? 0 : valorAtual;
  }

  validarValorUnitario(): void {
    const valorAtual = this.arredondarDuasCasas(Number(this.itemAta_insercao.valor_unitario) || 0);
    this.itemAta_insercao.valor_unitario = valorAtual < 0 ? 0 : valorAtual;
  }

  ngOnInit() {
    const id = Number(this.route.snapshot.queryParamMap.get('id'));

    if (!Number.isInteger(id) || id <= 0) {
      this.isLoadingPage = false;
      this.errorMessagePage = 'Não foi possível identificar o registro solicitado.';
      return;
    }

    this.idPagina = id;
    this.get(id, true);
    this.getEmpenho(id);
    this.getItens(id);
  }

  ngAfterViewInit() {
    const modalElement = this.modal.nativeElement;

    modalElement.addEventListener('shown.bs.modal', () => {
      this.input?.nativeElement?.focus();
    });

    modalElement.addEventListener('hide.bs.modal', (event: Event) => {
      if (this.permitirFecharModalSemConfirmacao) {
        this.permitirFecharModalSemConfirmacao = false;
        return;
      }

      if (this.isSaving) {
        event.preventDefault();
        return;
      }

      if (this.possuiDadosModalPreenchidos) {
        event.preventDefault();
        this.confirmarDescarteModal();
      }
    });
  }

  enviarPara(rota: string, id?: number) {
    if (id) {
      this.router.navigate([rota], { queryParams: { id } });
    } else {
      this.router.navigate([rota]);
    }
  }

  get(id: number, controlarEstadoPagina: boolean = false): void {
    if (controlarEstadoPagina) {
      this.isLoadingPage = true;
      this.errorMessagePage = '';
    }

    this.ataService.getById(id).subscribe({
      next: (resposta: Ata) => {
        this.ata = resposta;
        this.verificarValidade(this.ata);
        if (controlarEstadoPagina) {
          this.isLoadingPage = false;
        }
      },
      error: () => {
        if (controlarEstadoPagina) {
          this.isLoadingPage = false;
          this.errorMessagePage = 'Não foi possível carregar esta ata de registro de preços no momento.';
        }
      }
    });
  }

  recarregarPagina(): void {
    if (this.idPagina === null) {
      return;
    }

    this.get(this.idPagina, true);
    this.getEmpenho(this.idPagina);
    this.getItens(this.idPagina);
  }

  getEmpenho(ataId: number): void {
    this.isLoadingEmpenho = true;
    this.errorMessageEmpenho = '';

    this.ataService.getEmpenho(ataId).subscribe({
      next: (resposta: Empenho) => {
        this.empenho = resposta;
        this.isLoadingEmpenho = false;
      },
      error: () => {
        this.isLoadingEmpenho = false;
        this.errorMessageEmpenho = 'Não foi possível carregar o empenho vinculado.';
      }
    });
  }

  getItens(ataId: number): void {
    this.isLoadingItens = true;
    this.errorMessageItens = '';

    this.ataService.getItens(ataId).subscribe({
      next: (resposta: ItemEmpenho[]) => {
        this.itens = resposta;
        this.itemGenericoCadastrados = [];
        this.itens.forEach((item) => {
          this.itemGenericoCadastrados.push(item.item_ata.item_generico.id);
        });
        this.getItemGenerico();
        this.isLoadingItens = false;
      },
      error: () => {
        this.isLoadingItens = false;
        this.errorMessageItens = 'Não foi possível carregar os itens desta ARP.';
      }
    });
  }

  verificarItemCadastrado(itemGenericoId: number): boolean {
    return this.itemGenericoCadastrados.includes(itemGenericoId);
  }

  getItemGenerico(termobusca?: string): void {
    if (termobusca !== undefined) {
      this.termoBuscaItemGenerico = termobusca;
      this.currentPageItemGenerico = 1;
    }

    this.isLoadingItemGenerico = true;
    this.errorMessageItemGenerico = '';
    this.itemGenerico = [];
    this.carregarPaginaItemGenerico();
  }

  private carregarPaginaItemGenerico(page: number = 1, acumulados: ItemGenerico[] = []): void {
    this.itemGenericoService.get(this.termoBuscaItemGenerico, page, 100).subscribe({
      next: (resposta) => {
        const registros = [...acumulados, ...(resposta.results || [])];

        if (resposta.next) {
          this.carregarPaginaItemGenerico(page + 1, registros);
          return;
        }

        this.itemGenerico = registros.filter((item) => !this.verificarItemCadastrado(item.id));
        this.ajustarPaginaItemGenerico();
        this.isLoadingItemGenerico = false;
      },
      error: () => {
        this.itemGenerico = [];
        this.errorMessageItemGenerico = 'Não foi possível carregar os itens disponíveis no momento.';
        this.isLoadingItemGenerico = false;
      }
    });
  }

  private ajustarPaginaItemGenerico(): void {
    const totalPaginas = Math.max(1, Math.ceil(this.itemGenerico.length / this.pageSizeItemGenerico));

    if (this.currentPageItemGenerico > totalPaginas) {
      this.currentPageItemGenerico = totalPaginas;
    }
  }

  irParaPaginaItemGenerico(page: number): void {
    if (page === this.currentPageItemGenerico) {
      return;
    }

    this.currentPageItemGenerico = page;
  }

  verificarValidade(ata: Ata): string {
    const dataAtual = new Date();
    const dataAbertura = new Date(ata.licitacao.data_abertura);
    const validade = ata.licitacao.validade;
    const dataExpiracao = new Date(dataAbertura);
    dataExpiracao.setMonth(dataExpiracao.getMonth() + Number(validade));
    if (dataAtual > dataExpiracao) {
      this.validade = 'Expirado';
    } else {
      this.validade = 'Válido';
    }
    return this.validade;
  }

  classValidade(ata: Ata): string {
    if (this.verificarValidade(ata) === 'Válido') {
      return 'span-validade-valido';
    }
    return 'span-validade-expirado';
  }

  escolherItem(item: ItemGenerico): void {
    if (this.isSaving) {
      return;
    }

    this.itemGenerico_insercao.catmat = item.catmat;
    this.itemGenerico_insercao.descricao = item.descricao;
    this.itemGenerico_insercao.unidade_medida = item.unidade_medida;
    this.itemGenerico_insercao.categoria = item.categoria;
    this.itemAta_insercao.item_generico = item.id;
    this.jump_page = true;
    this.avanca_modal_page(2);
  }

  reiniciar_Modal(): void {
    if (this.isSaving) {
      return;
    }

    this.modal_page = 0;
    this.jump_page = false;
    this.formSubmittedPage1 = false;
    this.formSubmittedPage2 = false;
    this.errorMessageModal = '';
    this.errorMessageItemGenerico = '';
    this.termoBuscaItemGenerico = '';
    this.currentPageItemGenerico = 1;
    this.itemGenerico_insercao = <ItemGenerico>{ unidade_medida: '', categoria: '' };
    this.itemAta_insercao = <ItemAtaInsert>{ quantidade_licitada: 0, valor_unitario: 0 };
    this.getItemGenerico();
  }

  avanca_modal_page(valor?: number): void {
    if (this.isSaving) {
      return;
    }

    if (this.modal_page === 1 && valor === undefined) {
      this.formSubmittedPage1 = true;
      if (!this.itemGenericoFormValido) {
        return;
      }
    }

    this.modal_page = valor !== undefined ? valor : this.modal_page + 1;
  }

  volta_modal_page(valor?: number): void {
    if (this.isSaving) {
      return;
    }

    this.modal_page = valor !== undefined ? valor : this.modal_page - 1;
    if (this.jump_page == true) {
      this.jump_page = false;
      this.itemGenerico_insercao = <ItemGenerico>{ unidade_medida: '', categoria: '' };
      this.itemAta_insercao = <ItemAtaInsert>{ quantidade_licitada: 0, valor_unitario: 0 };
    }
  }

  getUnidadeMedida(item: ItemGenerico): string {
    const unidade = this.unidade_medida[item.unidade_medida as keyof typeof this.unidade_medida];
    return unidade ? unidade : item.unidade_medida;
  }

  getCategoria(item: ItemGenerico): string {
    const categoria = this.categoria[item.categoria as keyof typeof this.categoria];
    return categoria ? categoria : item.categoria;
  }

  saveItemGenerico(): void {
    this.formSubmittedPage1 = true;
    this.formSubmittedPage2 = true;
    this.errorMessageModal = '';

    if (this.isSaving || !this.itemGenericoFormValido || !this.itemAtaFormValido) {
      return;
    }

    this.isSaving = true;

    this.itemGenericoService.save(this.itemGenerico_insercao).subscribe({
      next: (resposta: ItemGenerico) => {
        this.itemAta_insercao.item_generico = resposta.id;
      },
      complete: () => {
        this.salvarItemAtaECriarEmpenho();
      },
      error: () => {
        this.isSaving = false;
        this.errorMessageModal = 'Não foi possível salvar o item genérico. Verifique os dados e tente novamente.';
      }
    });
  }

  saveItemAta(): void {
    this.formSubmittedPage2 = true;
    this.errorMessageModal = '';

    if (this.isSaving || !this.itemAtaFormValido) {
      return;
    }

    this.isSaving = true;
    this.salvarItemAtaECriarEmpenho();
  }

  private salvarItemAtaECriarEmpenho(): void {
    this.itemAta_insercao.ata = this.ata.id;

    this.itemAtaService.save(this.itemAta_insercao).subscribe({
      next: (resposta: ItemAtaInsert) => {
        this.itemEmpenho_insercao.item_ata = resposta.id;
        this.itemEmpenho_insercao.empenho = this.empenho.id;
        this.itemEmpenho_insercao.quantidade_atual = 0;
        this.itemEmpenho_insercao.quantidade_entrege = 0;
        this.saveItemEmpenho();
      },
      error: () => {
        this.isSaving = false;
        this.errorMessageModal = 'Não foi possível salvar o item na ata. Verifique os dados e tente novamente.';
      }
    });
  }

  saveItemEmpenho(): void {
    this.itemEmpenhoService.save(this.itemEmpenho_insercao).subscribe({
      next: (registro: ItemEmpenho) => {
        this.realizarOperacaoInsercao(registro.id);
      },
      error: () => {
        this.isSaving = false;
        this.errorMessageModal = 'Não foi possível registrar o item no empenho. Tente novamente.';
      }
    });
  }

  realizarOperacaoInsercao(id: number): void {
    this.operacaoInsercao.tipo = 'inc';
    this.operacaoInsercao.item_empenho = id;
    this.operacaoInsercao.valor = 1;
    this.operacaoInsercao.data = new Date();

    this.operacaService.save(this.operacaoInsercao).subscribe({
      next: () => {
        this.isSaving = false;
        this.fecharModalSemConfirmacao();
        this.feedback.sucesso('Item adicionado à ARP com sucesso.');
        this.get(this.ata.id);
        this.getEmpenho(this.ata.id);
        this.getItens(this.ata.id);
      },
      error: () => {
        this.isSaving = false;
        this.errorMessageModal = 'Não foi possível registrar a operação de inclusão. Tente novamente.';
      }
    });
  }

  tentarFecharModal(): void {
    if (this.isSaving) {
      return;
    }

    if (this.possuiDadosModalPreenchidos) {
      this.confirmarDescarteModal();
      return;
    }

    this.fecharModalSemConfirmacao();
  }

  private confirmarDescarteModal(): void {
    this.feedback.confirmar({
      titulo: 'Descartar alterações?',
      mensagem: 'Você já preencheu dados do item. Se sair agora, perderá toda a operação. Deseja sair mesmo assim?',
      textoConfirmar: 'Descartar',
      textoCancelar: 'Continuar editando',
      destrutiva: true
    }).then((desejaSair) => {
      if (desejaSair) {
        this.fecharModalSemConfirmacao();
      }
    });
  }

  private fecharModalSemConfirmacao(): void {
    if (this.fecharModalInternoBtn?.nativeElement) {
      this.permitirFecharModalSemConfirmacao = true;
      this.fecharModalInternoBtn.nativeElement.click();
    }
  }
}
