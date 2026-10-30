import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { ItemRecebimento } from '../../../model/estoque';
import { ItemOrdem } from '../../../model/itemOrdem';
import { OrdemEntrega } from '../../../model/ordem_entrega';
import { EstoqueService } from '../../../service/estoque.service';
import { OrdemEntregaService } from '../../../service/ordem-entrega.service';

interface LoteRecebimentoForm {
  numero_lote: string;
  data_validade: string;
  quantidade: number | null;
}

type ItemRecebimentoForm = ItemOrdem & {
  quantidade_pendente: number;
  lotes: LoteRecebimentoForm[];
};

@Component({
  selector: 'app-registrar-recebimento',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './registrar-recebimento.html',
  styleUrl: '../estoque.scss',
})
export class RegistrarRecebimento {
  ordem?: OrdemEntrega;
  itens: ItemRecebimentoForm[] = [];
  dataEntrada = this.agoraLocalParaInput();
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
        this.itens = itens.map(item => {
          const quantidade_pendente = Number(
            item.quantidade_pendente ?? (Number(item.quantidade_solicitada) - Number(item.quantidade_entregue)),
          );
          return {
            ...item,
            quantidade_pendente,
            lotes: quantidade_pendente > 0 ? [this.novoLote()] : [],
          };
        });
      },
      error: () => this.erro = 'Não foi possível carregar os itens da ordem.',
    });
  }

  get dataMinimaValidade(): string {
    return this.dataEntrada ? this.dataEntrada.slice(0, 10) : '';
  }

  /** Itens que continuarão com saldo a entregar e gerarão alerta para quem solicitou a ordem. */
  get itensQueFicaraoPendentes(): Array<{ descricao: string; unidade: string; faltante: number }> {
    return this.itens
      .map(item => ({
        descricao: item.item_empenho.item_ata.item_generico.descricao,
        unidade: item.item_empenho.item_ata.item_generico.unidade_medida,
        faltante: this.quantidadeRestante(item),
      }))
      .filter(item => item.faltante > 0);
  }

  novoLote(): LoteRecebimentoForm {
    return {
      numero_lote: '',
      data_validade: '',
      quantidade: null,
    };
  }

  adicionarLote(item: ItemRecebimentoForm): void {
    item.lotes.push(this.novoLote());
  }

  removerLote(item: ItemRecebimentoForm, index: number): void {
    item.lotes.splice(index, 1);
  }

  quantidadeReceber(item: ItemRecebimentoForm): number {
    const total = item.lotes.reduce((soma, lote) => {
      const quantidade = Number(lote.quantidade);
      return Number.isFinite(quantidade) && quantidade > 0 ? soma + quantidade : soma;
    }, 0);

    return this.arredondarQuantidade(total);
  }

  quantidadeRestante(item: ItemRecebimentoForm): number {
    return this.arredondarQuantidade(Math.max(this.quantidadePendente(item) - this.quantidadeReceber(item), 0));
  }

  preencherRestante(item: ItemRecebimentoForm, index: number): void {
    const quantidadeDasOutrasLinhas = item.lotes.reduce((soma, lote, indice) => {
      if (indice === index) return soma;
      const quantidade = Number(lote.quantidade);
      return Number.isFinite(quantidade) && quantidade > 0 ? soma + quantidade : soma;
    }, 0);
    const restante = Math.max(this.quantidadePendente(item) - quantidadeDasOutrasLinhas, 0);

    if (item.lotes[index] && restante > 0) {
      item.lotes[index].quantidade = this.arredondarQuantidade(restante);
    }
  }

  total(item: ItemRecebimentoForm): number {
    return this.quantidadeReceber(item) * Number(item.item_empenho.item_ata.valor_unitario);
  }

  mensagemValidadeProxima(lote: LoteRecebimentoForm): string {
    const dataMinima = this.dataMinimaValidade;
    if (!dataMinima || !lote.data_validade || lote.data_validade < dataMinima) return '';
    if (lote.data_validade === dataMinima) {
      return 'Atenção: este lote vence na data do recebimento.';
    }

    return lote.data_validade <= this.adicionarDias(dataMinima, 30)
      ? 'Atenção: este lote possui validade próxima.'
      : '';
  }

  confirmar(): void {
    if (!this.ordem || this.ordem.status === 'con') return;
    this.erro = '';
    const itens: ItemRecebimento[] = [];

    for (const item of this.itens) {
      const lotesParticipantes = item.lotes.filter(lote => this.linhaLotePreenchida(lote));
      if (!lotesParticipantes.length) continue;

      const numerosInformados = new Set<string>();
      const lotes: ItemRecebimento['lotes'] = [];
      for (const lote of lotesParticipantes) {
        const numero_lote = lote.numero_lote.trim();
        const quantidade = Number(lote.quantidade);

        if (!numero_lote || !lote.data_validade || !Number.isFinite(quantidade) || quantidade <= 0) {
          this.erro = 'Preencha número, validade e quantidade válida para cada lote informado.';
          return;
        }
        if (numero_lote.toLocaleLowerCase() === 'legado') {
          this.erro = 'O identificador LEGADO é reservado e não pode ser utilizado em novos recebimentos.';
          return;
        }
        if (this.dataMinimaValidade && lote.data_validade < this.dataMinimaValidade) {
          this.erro = 'A validade do lote não pode ser anterior à data do recebimento.';
          return;
        }

        const chaveLote = numero_lote.toLocaleLowerCase();
        if (numerosInformados.has(chaveLote)) {
          this.erro = 'O mesmo lote foi informado mais de uma vez para este item.';
          return;
        }
        numerosInformados.add(chaveLote);
        lotes.push({
          numero_lote,
          data_validade: lote.data_validade,
          quantidade,
        });
      }

      const quantidadeRecebida = this.quantidadeReceber(item);
      if (quantidadeRecebida > this.quantidadePendente(item)) {
        this.erro = 'A soma das quantidades dos lotes não pode exceder a quantidade pendente.';
        return;
      }
      const observacao = item.observacao || '';
      if (quantidadeRecebida < this.quantidadePendente(item) && !observacao.trim()) {
        this.erro = 'Informe o motivo da entrega parcial e da quantidade que continuará pendente.';
        return;
      }

      itens.push({
        item_ordem_id: item.id,
        lotes,
        observacao,
      });
    }

    if (!itens.length) {
      this.erro = 'Informe ao menos um lote válido para o recebimento.';
      return;
    }

    this.processando = true;
    this.estoqueService.receber(this.ordem.id, new Date(this.dataEntrada).toISOString(), itens).subscribe({
      next: () => this.router.navigate(['/estoque']),
      error: erro => {
        this.erro = this.mensagemErroApi(erro);
        this.processando = false;
      },
    });
  }

  private quantidadePendente(item: ItemRecebimentoForm): number {
    const quantidade = Number(item.quantidade_pendente);
    return Number.isFinite(quantidade) ? quantidade : 0;
  }

  private linhaLotePreenchida(lote: LoteRecebimentoForm): boolean {
    return lote.numero_lote.trim() !== '' || lote.data_validade !== '' || lote.quantidade !== null;
  }

  private arredondarQuantidade(quantidade: number): number {
    return Number.isFinite(quantidade) ? Number(quantidade.toFixed(3)) : 0;
  }

  private adicionarDias(data: string, dias: number): string {
    const [ano, mes, dia] = data.split('-').map(Number);
    if (!ano || !mes || !dia) return data;

    return new Date(Date.UTC(ano, mes - 1, dia + dias)).toISOString().slice(0, 10);
  }

  private mensagemErroApi(erro: unknown): string {
    const conteudo = erro && typeof erro === 'object' && 'error' in erro
      ? (erro as { error?: unknown }).error
      : erro;

    return this.primeiraMensagemTextual(conteudo) || 'Não foi possível registrar o recebimento.';
  }

  private primeiraMensagemTextual(valor: unknown): string | null {
    if (typeof valor === 'string' && valor.trim()) return valor;
    if (Array.isArray(valor)) {
      for (const item of valor) {
        const mensagem = this.primeiraMensagemTextual(item);
        if (mensagem) return mensagem;
      }
      return null;
    }
    if (valor && typeof valor === 'object') {
      for (const item of Object.values(valor as Record<string, unknown>)) {
        const mensagem = this.primeiraMensagemTextual(item);
        if (mensagem) return mensagem;
      }
    }
    return null;
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

