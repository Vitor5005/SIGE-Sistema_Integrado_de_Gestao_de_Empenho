import { Component, ElementRef, ViewChild } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { OrdemEntregaService } from '../../service/ordem-entrega.service';
import { OrdemEntrega } from '../../model/ordem_entrega';
import { ItemOrdemService } from '../../service/item-ordem.service';
import { ItemOrdem } from '../../model/itemOrdem';

@Component({
  selector: 'app-visualizar-entregas',
  imports: [BarraPesquisa, CommonModule],
  templateUrl: './visualizar-entregas.html',
  styleUrl: './visualizar-entregas.scss',
})
export class VisualizarEntregas {


  confirmado: boolean = false;

  constructor(
    private router: Router,
    private ordemEntregaService: OrdemEntregaService,
  ) { }

  entregas: OrdemEntrega[] = [];
  pedidosDaOrdem: ItemOrdem[] = [];

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
    this.ordemEntregaService.get(termobusca).subscribe({
      next: (registro: OrdemEntrega[]) => {
        this.entregas = registro;
      }
    });
  }

  getItensOrdem(id: number) {

    this.ordemEntregaService.getPedidos(id).subscribe({
      next: (registro: ItemOrdem[]) => {
        this.pedidosDaOrdem = registro;
      }
    })

  }

}
