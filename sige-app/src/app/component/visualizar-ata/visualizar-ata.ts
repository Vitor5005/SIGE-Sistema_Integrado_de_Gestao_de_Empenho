import { BotaoVoltar } from './../utils/botao-voltar/botao-voltar';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { Router, RouterLink, Route, ActivatedRoute, TitleStrategy } from '@angular/router';
import { AtaService } from '../../service/ata.service';
import { Ata } from '../../model/ata';
import { Fornecedor } from '../../model/fornecedor';
import { DecimalPipe, JsonPipe, KeyValuePipe } from '@angular/common';
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

@Component({
  selector: 'app-visualizar-ata',
  imports: [RouterLink, DecimalPipe, BotaoVoltar, FormsModule, BarraPesquisa, KeyValuePipe],
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
    private itemEmpenhoService: ItemEmpenhoService
  ) { }

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild("myInput") input!: ElementRef;

  ngOnInit() {

    const id = this.route.snapshot.queryParamMap.get('id');

    if (id) {
      this.get(Number(id))
      this.getEmpenho(Number(id));
      this.getItens(Number(id));
      this.getItemGenerico();
    }
  }

  ngAfterViewInit() {

    const modalElement = this.modal.nativeElement;

    modalElement.addEventListener('shown.bs.modal', () => {

      this.input.nativeElement.focus();

    });

  }

  ata: Ata = <Ata>{};
  empenho: Empenho = <Empenho>{};
  itens: Array<ItemEmpenho> = [];
  validade: string = "";
  itemGenerico: Array<ItemGenerico> = [];
  itemGenericoCadastrados: Array<number> = []; 

  modal_page: number = 0;
  jump_page: boolean = false;

  itemGenerico_insercao: ItemGenerico = <ItemGenerico>{
    unidade_medida: "",
    categoria: ""
  };
  itemAta_insercao: ItemAtaInsert = <ItemAtaInsert>{
    quantidade_licitada: 0,
    valor_unitario: 0,
  };
  itemEmpenho_insercao: ItemEmpenhoInsert = <ItemEmpenhoInsert>{};

  unidade_medida = {
    "KG": "Quilograma(KG)",
    "G": "Grama(G)",
    "L": "Litro(L)",
    "mL": "Mililitro(mL)",
    "duzia": "Duzia",
    "cento": "Cento",
    "PCT": "Pacote(PCT)",
    "CX": "Caixa(CX)",
    "FND": "Fardo(FND)",
    "GAR": "Garrafa(GAR)",
    "lata": "Lata",
    "un": "Unidade(UN)"
  };

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



  enviarPara(rota: string, id?: number) {
    if (id) {
      this.router.navigate([rota], { queryParams: { id } });
    }
    else {
      this.router.navigate([rota]);
    }
  }

  get(id: number) {
    this.ataService.getById(id).subscribe({
      next: (resposta: Ata) => {
        this.ata = resposta;
        this.verificarValidade(this.ata);
      }
    })
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
        this.itens.forEach(item => {
          (resposta: ItemEmpenho) => {
            this.itemGenericoCadastrados.push(resposta.item_ata.item_generico.id);
          }
        }
      )},
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
      this.validade = "Expirado";
    } else {
      this.validade = "Válido";
    }
    return this.validade;
  }

  classValidade(ata: Ata): string {
    if (this.verificarValidade(ata) === "Válido") {
      return "span-validade-valido";
    }
    return "span-validade-expirado";
  }

  escolherItem(item: ItemGenerico): void {
    this.itemGenerico_insercao.catmat = item.catmat;
    this.itemGenerico_insercao.descricao = item.descricao;
    this.itemGenerico_insercao.unidade_medida = item.unidade_medida;
    this.itemGenerico_insercao.categoria = item.categoria;
    this.itemAta_insercao.item_generico = item.id;
    this.jump_page = true;
    this.avanca_modal_page(2);
  }

  reiniciar_Modal(): void {
    this.modal_page = 0;
    this.jump_page = false;
    this.itemGenerico_insercao = <ItemGenerico>{ unidade_medida: "", categoria: "" };
    this.itemAta_insercao = <ItemAtaInsert>{ quantidade_licitada: 0, valor_unitario: 0 };
  }

  avanca_modal_page(valor?: number): void {
    this.modal_page = valor !== undefined ? valor : this.modal_page + 1;

  }

  volta_modal_page(valor?: number): void {
    this.modal_page = valor !== undefined ? valor : this.modal_page - 1;
    if (this.jump_page == true) {
      this.jump_page = false;
      this.itemGenerico_insercao = <ItemGenerico>{ unidade_medida: "", categoria: "" };
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
    this.itemGenericoService.save(this.itemGenerico_insercao).subscribe({
      next: (resposta: ItemGenerico) => {
        this.itemAta_insercao.item_generico = resposta.id;
      },
      complete: () => {
        this.saveItemAta();
      }
    });
  }

  saveItemAta(): void {
    this.itemAta_insercao.ata = this.ata.id;
    this.itemAtaService.save(this.itemAta_insercao).subscribe({
      next: (resposta: ItemAtaInsert) => {
        this.itemEmpenho_insercao.item_ata = resposta.id;
        this.itemEmpenho_insercao.empenho = this.empenho.id;
        this.itemEmpenho_insercao.quantidade_atual = 0;
        this.saveItemEmpenho();
      }
    });
  }

  saveItemEmpenho(): void {
    this.itemEmpenhoService.save(this.itemEmpenho_insercao).subscribe({
      complete: () => {
        this.atualizarAta();
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
      }
    });
  }
}
