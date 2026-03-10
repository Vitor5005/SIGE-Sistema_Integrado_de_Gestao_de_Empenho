import { Component, EventEmitter, Output } from '@angular/core';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/internal/operators/debounceTime';
import { distinctUntilChanged } from 'rxjs/internal/operators/distinctUntilChanged';

@Component({
  selector: 'app-barra-pesquisa',
  imports: [],
  templateUrl: './barra-pesquisa.html',
  styleUrl: './barra-pesquisa.scss',
})
export class BarraPesquisa {
  @Output() pesquisar = new EventEmitter<string>();
  private searchSubject = new Subject<string>(); 


  ngOnInit(): void {
    this.searchSubject.pipe(
      debounceTime(300), // Aguarda 300ms após parar de digitar
      distinctUntilChanged() // Só emite se o valor mudou
    ).subscribe(termo => {
      this.pesquisar.emit(termo);
    });
  }


  onPesquisar(event: Event): void {
    const termo = (event.target as HTMLInputElement).value;
    this.searchSubject.next(termo);
  }

}
