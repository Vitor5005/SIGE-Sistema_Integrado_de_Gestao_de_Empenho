import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { MovimentacaoEstoque } from '../../../model/estoque';
import { EstoqueService } from '../../../service/estoque.service';
import { Acao, pode, Recurso } from '../../../security/rbac';

@Component({
  selector: 'app-extrato-estoque',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './extrato-estoque.html',
  styleUrl: '../estoque.scss',
})
export class ExtratoEstoque {
  readonly pode = pode;
  readonly Acao = Acao;
  readonly Recurso = Recurso;

  generoId?: number;
  dataInicio = '';
  dataFim = '';
  movimentos: MovimentacaoEstoque[] = [];
  justificativa = '';
  erro = '';
  sucesso = '';

  constructor(private estoqueService: EstoqueService) {}

  ngOnInit(): void { this.carregar(); }

  carregar(): void {
    this.estoqueService.extrato(this.generoId, this.dataInicio || undefined, this.dataFim || undefined).subscribe({
      next: resposta => this.movimentos = resposta.results,
      error: () => this.erro = 'Não foi possível carregar o extrato.',
    });
  }

  estornar(movimento: MovimentacaoEstoque): void {
    const justificativa = prompt('Informe a justificativa obrigatória do estorno:');
    if (!justificativa?.trim()) return;
    this.estoqueService.estornar({ movimentacao_id: movimento.id, justificativa }).subscribe({
      next: () => {
        this.sucesso = 'Movimentação estornada com sucesso.';
        this.carregar();
      },
      error: erro => this.erro = erro.error?.detail || 'Não foi possível estornar a movimentação.',
    });
  }
}

