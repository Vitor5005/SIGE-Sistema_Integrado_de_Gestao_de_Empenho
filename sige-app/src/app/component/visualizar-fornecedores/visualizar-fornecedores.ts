import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Paginacao } from '../utils/paginacao/paginacao';
import { FornecedorService } from '../../service/fornecedor.service';
import { Fornecedor } from '../../model/fornecedor';
import { CommonModule, JsonPipe } from '@angular/common';

@Component({
  selector: 'app-visualizar-fornecedores',
  standalone: true,
  imports: [CommonModule, BarraPesquisa, Paginacao],
  templateUrl: './visualizar-fornecedores.html',
  styleUrl: './visualizar-fornecedores.scss',
})
export class VisualizarFornecedores {

  constructor(
    private router: Router,
    private fornecedorService: FornecedorService,
  ) { }

  fornecedores = Array<Fornecedor>()
  currentPage: number = 1;
  pageSize: number = 5;
  total: number = 0;
  hasNext: boolean = false;
  hasPrev: boolean = false;
  termoBuscaAtual: string = '';

  ngOnInit(){

    this.get()

  }

  enviarPara(rota: string, id?: number) {
    if (id) {
      this.router.navigate([rota], { queryParams: { id } });
    } else {
      this.router.navigate([rota]);
    }
  }

  get(termobusca?: string): void {
    if (termobusca !== undefined) {
      this.termoBuscaAtual = termobusca;
      this.currentPage = 1;
    }

    this.fornecedorService.get(this.termoBuscaAtual, this.currentPage, this.pageSize).subscribe(
      {
        next: (resposta) => {
          this.fornecedores = resposta.results
          this.total = resposta.count;
          this.hasNext = Boolean(resposta.next);
          this.hasPrev = Boolean(resposta.previous);
        }
      }
    )
  }

  proximaPagina(): void {
    if (!this.hasNext) {
      return;
    }

    this.currentPage += 1;
    this.get();
  }

  paginaAnterior(): void {
    if (!this.hasPrev || this.currentPage === 1) {
      return;
    }

    this.currentPage -= 1;
    this.get();
  }

  irParaPagina(page: number): void {
    if (page === this.currentPage) {
      return;
    }

    this.currentPage = page;
    this.get();
  }

}
