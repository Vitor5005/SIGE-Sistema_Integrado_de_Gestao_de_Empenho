import { FiltroConfig } from './../../../model/filtro-config';
import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, input, output, Output } from '@angular/core';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/internal/operators/debounceTime';
import { distinctUntilChanged } from 'rxjs/internal/operators/distinctUntilChanged';

@Component({
  selector: 'app-barra-pesquisa',
  standalone: true,
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

  filtrosLicitacoes: FiltroConfig[] = [
    {
      campo: 'data_abertura',
      label: 'Período da venda',
      tipo: 'date-range'
    }
  ];

  ngOnInit(): void {
    this.searchSubject.pipe(debounceTime(300), distinctUntilChanged()).subscribe((termo) => {
      this.pesquisar.emit(termo);
    });
  }

  onPesquisar(event: Event): void {
    const termo = (event.target as HTMLInputElement).value;
    this.searchSubject.next(termo);
  }

  alterarFiltro(campo: string, valor: any, evento?: Event) {

    const checkbox = evento?.target as HTMLInputElement;

    if (checkbox && checkbox.type === 'checkbox') {

      if (!this.valores[campo]) {
        this.valores[campo] = [];
      }

      if (checkbox.checked) {
        this.valores[campo].push(valor);
      } else {
        this.valores[campo] = this.valores[campo].filter((v: any) => v !== valor);
      }

      if (this.valores[campo].length === 0) {
        delete this.valores[campo];
      }

    } else {

      if (valor === null || valor === '') {
        delete this.valores[campo];
      } else {
        this.valores[campo] = valor;
      }

    }

    this.filtrosAlterados.emit(this.valores);
  }

  limparFiltros() {
    this.valores = {};
    this.filtrosAlterados.emit(this.valores);
  }
}
