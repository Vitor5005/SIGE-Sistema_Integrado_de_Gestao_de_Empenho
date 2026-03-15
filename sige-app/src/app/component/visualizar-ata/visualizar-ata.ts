import { BotaoVoltar } from './../utils/botao-voltar/botao-voltar';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { AtaService } from '../../service/ata.service';
import { Ata } from '../../model/ata';
import { DecimalPipe, KeyValuePipe } from '@angular/common';
import { Empenho } from '../../model/empenho';
import { ItemAta } from '../../model/itemAta';
import { ItemEmpenho } from '../../model/itemEmpenho';
import { FormsModule } from '@angular/forms';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { ItemGenericoService } from '../../service/item-generico.service';
import { ItemGenerico } from '../../model/item_generico';
import { ItemAtaService } from '../../service/item-ata.service';
import { ItemEmpenhoService } from '../../service/item-empenho.service';
import { ItemAtaInsert } from '../../model/itemAta_insert';
import { ItemEmpenhoInsert } from '../../model/itemEmpenho_insert';
import { OperacaoItemService } from '../../service/operacao-item.service';
import { OperacaoItemInsert } from '../../model/operacao_item_insert';

@Component({
  selector: 'app-visualizar-ata',
  imports: [DecimalPipe, BotaoVoltar, FormsModule, BarraPesquisa, KeyValuePipe],
  templateUrl: './visualizar-ata.html',
  styleUrl: './visualizar-ata.scss',
})
export class VisualizarAta {

  constructor(
    private router: Router,
    private ataService: AtaService,
    private route: ActivatedRoute,
    private itemGenericoService: ItemGenericoService,
    private itemAtaService: ItemAtaService,
    private itemEmpenhoService: ItemEmpenhoService,
    private operacaService: OperacaoItemService
  ) { }

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild('myInput') input!: ElementRef;
  @ViewChild('fecharModalInternoBtn') fecharModalInternoBtn!: ElementRef<HTMLButtonElement>;

  ata: Ata = <Ata>{};
  empenho: Empenho = <Empenho>{};
  itens: Array<ItemEmpenho> = [];
  validade: string = '';
  itemGenerico: Array<ItemGenerico> = [];
  itemGenericoCadastrados: Array<number> = [];
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
    const id = this.route.snapshot.queryParamMap.get('id');

    if (id) {
      this.get(Number(id));
      this.getEmpenho(Number(id));
      this.getItens(Number(id));
      this.getItemGenerico();
    }
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
        const desejaSair = confirm('Você já preencheu dados do item. Se sair agora, perderá toda a operação. Deseja sair mesmo assim?');
        if (!desejaSair) {
          event.preventDefault();
        }
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

  get(id: number) {
    this.ataService.getById(id).subscribe({
      next: (resposta: Ata) => {
        this.ata = resposta;
        this.verificarValidade(this.ata);
      }
    });
  }

  getEmpenho(ataId: number): void {
    this.ataService.getEmpenho(ataId).subscribe({
      next: (resposta: Empenho) => {
        this.empenho = resposta;
      },
    });
  }

  getItens(ataId: number): void {
    this.ataService.getItens(ataId).subscribe({
      next: (resposta: ItemEmpenho[]) => {
        this.itens = resposta;
        this.itemGenericoCadastrados = [];
        this.itens.forEach((item) => {
          this.itemGenericoCadastrados.push(item.item_ata.item_generico.id);
        });
      },
    });
  }

  verificarItemCadastrado(itemGenericoId: number): boolean {
    return this.itemGenericoCadastrados.includes(itemGenericoId);
  }

  getItemGenerico(): void {
    this.itemGenericoService.get().subscribe({
      next: (resposta: ItemGenerico[]) => {
        this.itemGenerico = resposta;
      },
    });
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
    this.itemGenerico_insercao = <ItemGenerico>{ unidade_medida: '', categoria: '' };
    this.itemAta_insercao = <ItemAtaInsert>{ quantidade_licitada: 0, valor_unitario: 0 };
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
    this.itemAta_insercao.quantidade_licitada = Number(this.itemAta_insercao.quantidade_licitada) - 1;

    this.itemAtaService.save(this.itemAta_insercao).subscribe({
      next: (resposta: ItemAtaInsert) => {
        this.itemEmpenho_insercao.item_ata = resposta.id;
        this.itemEmpenho_insercao.empenho = this.empenho.id;
        this.itemEmpenho_insercao.quantidade_atual = 1;
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
      complete: () => {
        this.atualizarAta();
      },
      error: () => {
        this.isSaving = false;
        this.errorMessageModal = 'Não foi possível registrar a operação de inclusão. Tente novamente.';
      }
    });
  }

  atualizarAta(): void {
    const valorTotal = Number(this.itemAta_insercao.valor_unitario) * Number(this.itemAta_insercao.quantidade_licitada);
    const saldoAtual = Number(this.ata.ata_saldo_total) || 0;
    this.ata.ata_saldo_total = Number((saldoAtual + valorTotal).toFixed(2));

    this.ataService.patch(this.ata.id, { ata_saldo_total: this.ata.ata_saldo_total }).subscribe({
      complete: () => {
        alert('Item cadastrado com sucesso!');
        window.location.reload();
      },
      error: () => {
        this.isSaving = false;
        this.errorMessageModal = 'Item salvo, mas houve erro ao atualizar saldo da ata.';
      }
    });
  }

  tentarFecharModal(): void {
    if (this.isSaving) {
      return;
    }

    if (this.possuiDadosModalPreenchidos) {
      const desejaSair = confirm('Você já preencheu dados do item. Se sair agora, perderá toda a operação. Deseja sair mesmo assim?');
      if (!desejaSair) {
        return;
      }
    }

    if (this.fecharModalInternoBtn?.nativeElement) {
      this.permitirFecharModalSemConfirmacao = true;
      this.fecharModalInternoBtn.nativeElement.click();
    }
  }
}
