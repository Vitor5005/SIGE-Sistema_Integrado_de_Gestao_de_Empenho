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

@Component({
  selector: 'app-visualizar-empenho',
  imports: [BotaoVoltar, CommonModule, FormsModule],
  templateUrl: './visualizar-empenho.html',
  styleUrl: './visualizar-empenho.scss',
})
export class VisualizarEmpenho {
  tipo: 'reforco' | 'anulacao' = 'reforco';
  constructor(
    private router: Router,
    private empenhoService: EmpenhoService,
    private operacaoItemService: OperacaoItemService,
    private ataService: AtaService,
    private itemAtaService: ItemAtaService,
    private itemEmpenhoService: ItemEmpenhoService,
    private route: ActivatedRoute
  ) { }

  empenho: Empenho = <Empenho>{};
  itensEmpenho: ItemEmpenho[] = [];
  itemEmpenhoModal: ItemEmpenho = <ItemEmpenho>{};

  operacoesEmpenho: OperacaoItem[] = [];
  operacaoItem_insercao: OperacaoItemInsert = <OperacaoItemInsert>{ data: new Date().toISOString().split('T')[0], tipo: 'inc', item_empenho: 0, valor: 0 };

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

  carregarItemEmpenho(item: ItemEmpenho) {
    this.itemEmpenhoModal = item;
    this.operacaoItem_insercao.item_empenho = item.id;
  }

  trocarOperacao(tipo: string): void {
    this.operacaoItem_insercao.tipo = tipo;
  }

  salvarOperacaoItem(): void {
    this.operacaoItem_insercao.data = new Date().toISOString().split('T')[0];
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

}
