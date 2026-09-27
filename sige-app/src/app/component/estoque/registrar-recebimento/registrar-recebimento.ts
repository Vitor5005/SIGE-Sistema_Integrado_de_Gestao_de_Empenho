import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { ItemOrdem } from '../../../model/itemOrdem';
import { OrdemEntrega } from '../../../model/ordem_entrega';
import { EstoqueService } from '../../../service/estoque.service';
import { OrdemEntregaService } from '../../../service/ordem-entrega.service';

@Component({
  selector: 'app-registrar-recebimento',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './registrar-recebimento.html',
  styleUrl: '../estoque.scss',
})
export class RegistrarRecebimento {
  ordem?: OrdemEntrega;
  itens: Array<ItemOrdem & { quantidade_pendente: number; quantidade_receber: number }> = [];
  dataEntrada = new Date().toISOString().slice(0, 16);
  processando = false;
  erro = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private ordemService: OrdemEntregaService,
    private estoqueService: EstoqueService,
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.queryParamMap.get('id'));
    if (!id) {
      this.erro = 'Ordem de entrega não informada.';
      return;
    }
    this.ordemService.getById(id).subscribe({
      next: ordem => {
        this.ordem = ordem;
        if (ordem.status === 'con') this.erro = 'Esta ordem já foi concluída.';
      },
      error: () => this.erro = 'Não foi possível carregar a ordem.',
    });
    this.ordemService.getPedidos(id).subscribe({
      next: itens => {
        this.itens = itens.map(item => ({
          ...item,
          quantidade_pendente: Number(item.quantidade_pendente ?? (Number(item.quantidade_solicitada) - Number(item.quantidade_entregue))),
          quantidade_receber: 0,
        }));
      },
      error: () => this.erro = 'Não foi possível carregar os itens da ordem.',
    });
  }

  total(item: ItemOrdem & { quantidade_receber: number }): number {
    return Number(item.quantidade_receber || 0) * Number(item.item_empenho.item_ata.valor_unitario);
  }

  confirmar(): void {
    if (!this.ordem || this.ordem.status === 'con') return;
    const itens = this.itens
      .filter(item => Number(item.quantidade_receber) > 0)
      .map(item => ({
        item_ordem_id: item.id,
        quantidade_recebida: Number(item.quantidade_receber),
        observacao: item.observacao || '',
      }));
    const invalido = itens.some(item => {
      const original = this.itens.find(i => i.id === item.item_ordem_id);
      return !original || item.quantidade_recebida > Number(original.quantidade_pendente);
    });
    const parcialSemMotivo = itens.some(item => {
      const original = this.itens.find(i => i.id === item.item_ordem_id);
      return original && item.quantidade_recebida < Number(original.quantidade_pendente) && !item.observacao.trim();
    });
    if (!itens.length || invalido) {
      this.erro = 'Informe pelo menos uma quantidade válida, sem exceder o saldo pendente.';
      return;
    }
    if (parcialSemMotivo) {
      this.erro = 'Informe o motivo da entrega parcial e da quantidade que continuará pendente.';
      return;
    }
    this.processando = true;
    this.estoqueService.receber(this.ordem.id, new Date(this.dataEntrada).toISOString(), itens).subscribe({
      next: () => this.router.navigate(['/estoque']),
      error: erro => {
        const valor = erro.error && Object.values(erro.error)[0];
        this.erro = Array.isArray(valor) ? String(valor[0]) : 'Não foi possível registrar o recebimento.';
        this.processando = false;
      },
    });
  }
}

