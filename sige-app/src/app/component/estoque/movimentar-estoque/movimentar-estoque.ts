import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { EstoqueItem } from '../../../model/estoque';
import { EstoqueService } from '../../../service/estoque.service';

@Component({
  selector: 'app-movimentar-estoque',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './movimentar-estoque.html',
  styleUrl: '../estoque.scss',
})
export class MovimentarEstoque {
  operacao: 'SAIDA' | 'CARGA_INICIAL' | 'AJUSTE' = 'SAIDA';
  itens: EstoqueItem[] = [];
  itemGenericoId?: number;
  quantidade?: number;
  tipoSaida = 'PRODUCAO';
  justificativa = '';
  dataHora = this.agoraLocalParaInput();
  processando = false;
  erro = '';
  sucesso = '';

  constructor(private estoqueService: EstoqueService) {}

  ngOnInit(): void {
    this.estoqueService.listar('', 1, 100).subscribe(resposta => this.itens = resposta.results);
  }

  salvar(): void {
    if (!this.itemGenericoId || !this.quantidade || !this.justificativa.trim()) {
      this.erro = 'Preencha gênero, quantidade e justificativa.';
      return;
    }
    this.processando = true;
    this.erro = '';
    const base = {
      item_generico_id: this.itemGenericoId,
      justificativa: this.justificativa,
      data_hora: new Date(this.dataHora).toISOString(),
    };
    const requisicao = this.operacao === 'SAIDA'
      ? this.estoqueService.registrarSaida({ ...base, quantidade: this.quantidade, tipo_saida: this.tipoSaida })
      : this.operacao === 'CARGA_INICIAL'
        ? this.estoqueService.registrarCargaInicial({ ...base, quantidade: this.quantidade })
        : this.estoqueService.registrarAjuste({ ...base, quantidade_ajuste: this.quantidade });

    requisicao.subscribe({
      next: () => {
        this.sucesso = 'Movimentação registrada com sucesso.';
        this.processando = false;
        this.quantidade = undefined;
        this.justificativa = '';
      },
      error: erro => {
        this.erro = this.mensagemErro(erro.error);
        this.processando = false;
      },
    });
  }

  private mensagemErro(erro: any): string {
    if (!erro) return 'Não foi possível registrar a movimentação.';
    const valor = Object.values(erro)[0];
    return Array.isArray(valor) ? String(valor[0]) : String(valor);
  }

  private agoraLocalParaInput(): string {
    const agora = new Date();
    const ano = agora.getFullYear();
    const mes = String(agora.getMonth() + 1).padStart(2, '0');
    const dia = String(agora.getDate()).padStart(2, '0');
    const hora = String(agora.getHours()).padStart(2, '0');
    const minuto = String(agora.getMinutes()).padStart(2, '0');

    return `${ano}-${mes}-${dia}T${hora}:${minuto}`;
  }
}

