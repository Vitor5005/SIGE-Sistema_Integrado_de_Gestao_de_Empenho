import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, input, output, Output } from '@angular/core';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/internal/operators/debounceTime';
import { distinctUntilChanged } from 'rxjs/internal/operators/distinctUntilChanged';

@Component({
  selector: 'app-barra-pesquisa',
  imports: [CommonModule],
  templateUrl: './barra-pesquisa.html',
  styleUrl: './barra-pesquisa.scss',
})
export class BarraPesquisa {
  @Input() filtros: any[] = []

  @Output() pesquisar = new EventEmitter<string>();
  private searchSubject = new Subject<string>();
  @Output() aplicarFiltro = new EventEmitter<any>();

  @Input() filtrosLicitacao: any[] = [];
  @Output() filtrarLicitacao = new EventEmitter<number>();
  
  ngOnInit(): void {
    this.searchSubject.pipe(
      debounceTime(300), // Aguarda 300ms após parar de digitar
      distinctUntilChanged() // Só emite se o valor mudou
    ).subscribe(termo => {
      this.pesquisar.emit(termo);
    });
  }

  onFiltroClick(filtro: any){
    this.aplicarFiltro.emit(filtro)
  }

  onPesquisar(event: Event): void {
    const termo = (event.target as HTMLInputElement).value;
    this.searchSubject.next(termo);
  }

}
