import { FiltroConfig } from './../../model/filtro-config';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { OrdemEntregaService } from '../../service/ordem-entrega.service';
import { OrdemEntrega } from '../../model/ordem_entrega';
import { ItemOrdemService } from '../../service/item-ordem.service';
import { ItemOrdem } from '../../model/itemOrdem';
import { ItemOrdemInsert } from '../../model/itemOrdem_insert';
import { FormsModule } from '@angular/forms';
import { forkJoin, Observable, of, switchMap } from 'rxjs';
import { EmpenhoService } from '../../service/empenho.service';
import { ItemEmpenhoService } from '../../service/item-empenho.service';

@Component({
  selector: 'app-visualizar-entregas',
  imports: [BarraPesquisa, CommonModule, FormsModule],
  templateUrl: './visualizar-entregas.html',
  styleUrl: './visualizar-entregas.scss',
})
export class VisualizarEntregas {

  filtros: FiltroConfig[] = [
  {
    campo: 'status',
    label: 'Status da entrega',
    tipo: 'radio',
    opcoes: [
      { valor: 'esp', label: 'Entrega em espera' },
      { valor: 'con', label: 'Entrega realizada' }
    ]
  },
  {
    campo: 'data_emissao',
    label: 'Data de emissão',
    tipo: 'date-range'
  }
];

filtrosAtivos: any = {};

  confirmado: boolean = false;

  constructor(
    private router: Router,
    private ordemEntregaService: OrdemEntregaService,
    private itensOrdemService: ItemOrdemService,
    private empenhoService: EmpenhoService,
    private itemEmpenhoService: ItemEmpenhoService
  ) { }

  entregas: OrdemEntrega[] = [];
  pedidosDaOrdem: ItemOrdem[] = [];
  ordemSelecionada: number = 0;

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

  ngOnInit() {
    this.getEntregas();
  }

  ngAfterViewInit() {

    const modalElement = this.modal.nativeElement;

    modalElement.addEventListener('shown.bs.modal', () => {
      this.input.nativeElement.focus();
    });

  }

  getEntregas(termobusca?: string) {

    const params = { ...this.filtrosAtivos };

    if (termobusca) {
      params['search'] = termobusca;
    }

    this.ordemEntregaService.getComFiltros(params).subscribe({
      next: (registro: OrdemEntrega[]) => {
        this.entregas = this.ordenarEntregaPorStatusEData(registro);
      }
    });

  }

  getItensOrdem(id: number, index: number) {
    this.ordemSelecionada = index;
    this.ordemEntregaService.getPedidos(id).subscribe({
      next: (registro: ItemOrdem[]) => {
        this.pedidosDaOrdem = registro;
      }
    });

  }

  verificarStatus(status: string): string {
    if (status === "esp") {
      return "Entrega em espera";
    }
    return "Entrega realizada";
  }

  classeStatus(status: string): string {
    if (status === "esp") {
      return "em_espera";
    }
    return "realizada";
  }

  ordenarEntregaPorStatusEData(entregas: OrdemEntrega[]): OrdemEntrega[] {
    return entregas.sort((a, b) => {
      if (a.status === b.status) {
        return new Date(a.data_emissao).getTime() - new Date(b.data_emissao).getTime();
      }
      return a.status === 'esp' ? -1 : 1;
    });
  }

  verificarQuantidadeEntregue(item: ItemOrdem) {
    if (item.quantidade_entregue > item.quantidade_solicitada) {
      item.quantidade_entregue = item.quantidade_solicitada;
    }

    if (item.quantidade_entregue < 0) {
      item.quantidade_entregue = 0;
    }
  }

  confirmarEntrega(ordemIndex: number): void {
    const ordem = this.entregas[ordemIndex];
    const somaValorEntregue = this.calcularSomaValorEntregue(this.pedidosDaOrdem);

    this.atualizarItensDaOrdem(this.pedidosDaOrdem).pipe(
      switchMap(() => this.atualizarOrdemComoConcluida(ordem.id)),
      switchMap(() => this.atualizarSaldoEmpenho(ordem.empenho.id, ordem.empenho.saldo_utilizado, somaValorEntregue))
    ).subscribe({
      complete: () => window.location.reload(),
      error: (err) => console.error('Erro ao confirmar entrega', err)
    });
  }

  private calcularSomaValorEntregue(itens: ItemOrdem[]): number {
    return itens.reduce((acc, item) => {
      const valorItem = Number(
        (Number(item.item_empenho.item_ata.valor_unitario) * Number(item.quantidade_entregue)).toFixed(2)
      );
      return Number((acc + valorItem).toFixed(2));
    }, 0);
  }

  private atualizarItensDaOrdem(itens: ItemOrdem[]): Observable<any> {
    if (!itens.length) return of(null);

    const requests = itens.map(item => {
      const itemUpdate = {
        quantidade_entregue: item.quantidade_entregue,
        observacao: item.observacao
      };

      const itemEmpenhoUpdate = {
        quantidade_entrege: item.quantidade_entregue
      };

      return this.itensOrdemService.patch(item.id, itemUpdate).pipe(
        switchMap(() =>
          this.itemEmpenhoService.patch(item.item_empenho.id, itemEmpenhoUpdate)
        )
      );
    });

    return forkJoin(requests);
  }

  private atualizarOrdemComoConcluida(ordemId: number): Observable<any> {
    const ordemUpdate = {
      status: 'con',
      data_entrega: new Date()
    };
    return this.ordemEntregaService.patch(ordemId, ordemUpdate);
  }

  private atualizarSaldoEmpenho(empenhoId: number, saldoAtual: number, somaValorEntregue: number): Observable<any> {
    const novoSaldo = Number((Number(saldoAtual) + somaValorEntregue).toFixed(2));
    return this.empenhoService.patch(empenhoId, { saldo_utilizado: novoSaldo });
  }

  aplicarFiltros(filtros: any) {
    this.filtrosAtivos = filtros;
    this.getEntregas();
  }
}
