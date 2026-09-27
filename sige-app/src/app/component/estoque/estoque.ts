import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { EstoqueConsolidado, EstoqueItem } from '../../model/estoque';
import { EstoqueService } from '../../service/estoque.service';
import { Acao, pode, Recurso } from '../../security/rbac';

@Component({
  selector: 'app-estoque',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './estoque.html',
  styleUrl: './estoque.scss',
})
export class Estoque {
  readonly pode = pode;
  readonly Acao = Acao;
  readonly Recurso = Recurso;

  itens: EstoqueItem[] = [];
  consolidado: EstoqueConsolidado[] = [];
  busca = '';
  categoria = '';
  agruparPorCategoria = false;
  carregando = false;
  erro = '';

  constructor(private estoqueService: EstoqueService) {}

  ngOnInit(): void {
    this.carregar();
    if (pode(Recurso.ESTOQUE, Acao.CONSULTAR_CONSOLIDADO)) {
      this.estoqueService.consolidado().subscribe({
        next: dados => this.consolidado = dados,
        error: () => this.erro = 'Não foi possível carregar a visão consolidada.',
      });
    }
  }

  carregar(): void {
    this.carregando = true;
    this.estoqueService.listar(this.busca, 1, 100, this.categoria).subscribe({
      next: resposta => {
        this.itens = resposta.results;
        this.carregando = false;
      },
      error: () => {
        this.erro = 'Não foi possível carregar o estoque.';
        this.carregando = false;
      },
    });
  }

  alternarAgrupamento(): void {
    this.agruparPorCategoria = !this.agruparPorCategoria;
    if (this.agruparPorCategoria) {
      this.itens = [...this.itens].sort((a, b) =>
        a.categoria_descricao.localeCompare(b.categoria_descricao)
        || a.descricao.localeCompare(b.descricao)
      );
    }
  }

  iniciaCategoria(index: number): boolean {
    return this.agruparPorCategoria && (
      index === 0 || this.itens[index - 1].categoria !== this.itens[index].categoria
    );
  }
}

