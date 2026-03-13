import { FiltroConfig } from './../../../model/filtro-config';
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
  @Input() filtros: FiltroConfig[] = [];

  @Output() pesquisar = new EventEmitter<string>();
  @Output() filtrosAlterados = new EventEmitter<any>();

  private searchSubject = new Subject<string>();

  valores: any = {};

  ngOnInit(): void {
    this.searchSubject.pipe(debounceTime(300), distinctUntilChanged()).subscribe((termo) => {
      this.pesquisar.emit(termo);
    });
  }

  onPesquisar(event: Event): void {
    const termo = (event.target as HTMLInputElement).value;
    this.searchSubject.next(termo);
  }

  alterarFiltro(campo: string, valor: any) {
    if (valor === null || valor === '') {
      delete this.valores[campo];
    } else {
      this.valores[campo] = valor;
    }

    this.filtrosAlterados.emit(this.valores);
  }
  limparFiltros() {
    this.valores = {};
    this.filtrosAlterados.emit(this.valores);
  }
}
