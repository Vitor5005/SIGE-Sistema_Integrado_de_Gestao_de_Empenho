import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { EstoqueItem } from '../../../model/estoque';
import { EstoqueService } from '../../../service/estoque.service';

type Operacao = 'SAIDA' | 'INVENTARIO' | 'CARGA_INICIAL';

const DESCRICOES: Record<Operacao, string> = {
  SAIDA: 'Retira do estoque o que foi consumido, doado ou perdido.',
  INVENTARIO: 'Informe o que foi contado na prateleira; o sistema lança a diferença para o saldo atual.',
  CARGA_INICIAL: 'Registra o saldo que já existia antes do sistema. Feita uma única vez por gênero.',
};

@Component({
  selector: 'app-movimentar-estoque',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './movimentar-estoque.html',
  styleUrl: '../estoque.scss',
})
export class MovimentarEstoque {
  operacao: Operacao = 'SAIDA';
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
    this.carregarItens();
  }

  get itensSemCargaInicial(): EstoqueItem[] {
    return this.itens.filter(item => !item.possui_carga_inicial);
  }

  get itensDaOperacao(): EstoqueItem[] {
    return this.operacao === 'CARGA_INICIAL' ? this.itensSemCargaInicial : this.itens;
  }

  get itemSelecionado(): EstoqueItem | undefined {
    return this.itens.find(item => item.item_generico_id === this.itemGenericoId);
  }

  get descricaoOperacao(): string {
    return DESCRICOES[this.operacao];
  }

  get rotuloQuantidade(): string {
    return this.operacao === 'INVENTARIO' ? 'Quantidade contada' : 'Quantidade';
  }

  get diferencaInventario(): number | null {
    if (!this.itemSelecionado || this.quantidade === undefined || this.quantidade === null) {
      return null;
    }
    return Number(this.quantidade) - Number(this.itemSelecionado.saldo_atual);
  }

  get diferencaAbsoluta(): number {
    return Math.abs(this.diferencaInventario ?? 0);
  }

  trocarOperacao(operacao: Operacao): void {
    this.operacao = operacao;
    this.erro = '';
    this.sucesso = '';
    if (!this.itensDaOperacao.some(item => item.item_generico_id === this.itemGenericoId)) {
      this.itemGenericoId = undefined;
    }
  }

  salvar(): void {
    if (!this.itemGenericoId || this.quantidade === undefined || this.quantidade === null || !this.justificativa.trim()) {
      this.erro = 'Preencha gênero, quantidade e justificativa.';
      return;
    }
    this.processando = true;
    this.erro = '';
    this.sucesso = '';
    const base = {
      item_generico_id: this.itemGenericoId,
      justificativa: this.justificativa,
      data_hora: new Date(this.dataHora).toISOString(),
    };
    const requisicao = this.operacao === 'SAIDA'
      ? this.estoqueService.registrarSaida({ ...base, quantidade: this.quantidade, tipo_saida: this.tipoSaida })
      : this.operacao === 'CARGA_INICIAL'
        ? this.estoqueService.registrarCargaInicial({ ...base, quantidade: this.quantidade })
        : this.estoqueService.registrarAjuste({ ...base, quantidade_contada: this.quantidade });
    requisicao.subscribe({
      next: () => {
        this.sucesso = 'Movimentação registrada com sucesso.';
        this.processando = false;
        this.quantidade = undefined;
        this.justificativa = '';
        this.carregarItens();
      },
      error: erro => {
        this.erro = this.mensagemErro(erro.error);
        this.processando = false;
      },
    });
  }

  private carregarItens(): void {
    this.estoqueService.listar('', 1, 100).subscribe(resposta => {
      this.itens = resposta.results;
      if (this.operacao === 'CARGA_INICIAL' && !this.itensSemCargaInicial.length) {
        this.trocarOperacao('SAIDA');
      } else if (!this.itensDaOperacao.some(item => item.item_generico_id === this.itemGenericoId)) {
        this.itemGenericoId = undefined;
      }
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
