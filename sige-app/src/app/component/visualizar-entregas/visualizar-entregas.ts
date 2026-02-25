import { Component, ElementRef, ViewChild } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-visualizar-entregas',
  imports: [BarraPesquisa, CommonModule],
  templateUrl: './visualizar-entregas.html',
  styleUrl: './visualizar-entregas.scss',
})
export class VisualizarEntregas {


  confirmado: boolean = false;

  constructor(private router: Router) { }

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild('myInput') input!: ElementRef;

  enviarPara(rota: string) {
    this.router.navigate([rota]);
  }

  ngAfterViewInit() {

    const modalElement = this.modal.nativeElement;

    modalElement.addEventListener('shown.bs.modal', () => {
      this.input.nativeElement.focus();
    });

  }


}
