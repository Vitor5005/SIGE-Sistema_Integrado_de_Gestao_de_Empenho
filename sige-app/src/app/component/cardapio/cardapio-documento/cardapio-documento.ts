import { DatePipe, UpperCasePipe } from '@angular/common';
import { Component, Input } from '@angular/core';

import { Cardapio, ItemCardapio } from '../../../model/cardapio';
import { agruparPorSecao, formatarQuantidade } from '../cardapio-util';

/** Cardápio quantitativo no mesmo modelo da folha impressa usada pelo Restaurante Universitário. */
@Component({
  selector: 'app-cardapio-documento',
  imports: [DatePipe, UpperCasePipe],
  templateUrl: './cardapio-documento.html',
  styleUrl: './cardapio-documento.scss',
})
export class CardapioDocumento {
  @Input({ required: true }) cardapio!: Cardapio;

  get preparacoes(): string[] {
    return this.cardapio.preparacoes.split('\n').map((linha) => linha.trim()).filter(Boolean);
  }

  get grupos(): { secao: string; itens: ItemCardapio[] }[] {
    return agruparPorSecao(this.cardapio.itens);
  }

  /** Data no formato "2025-09-29" interpretada no fuso local (evita voltar um dia). */
  get dataLocal(): Date {
    const [ano, mes, dia] = this.cardapio.data.split('-').map(Number);
    return new Date(ano, mes - 1, dia);
  }

  quantidadeTexto(valor: number | string | null | undefined, item: ItemCardapio): string {
    return `${formatarQuantidade(valor)} ${(item.unidade_medida || '').toLowerCase()}`.trim();
  }

  /** A quantidade liberada pelo estoque substitui a planejada, como as correções feitas à mão na folha. */
  liberadaDiferente(item: ItemCardapio): boolean {
    return item.quantidade_liberada !== null && item.quantidade_liberada !== undefined
      && Number(item.quantidade_liberada) !== Number(item.quantidade_planejada);
  }

  genero(item: ItemCardapio): string {
    if (!item.conteudo_embalagem) {
      return item.descricao || '';
    }
    const conteudo = Number(item.conteudo_embalagem).toLocaleString('pt-BR', { maximumFractionDigits: 3 });
    return `${item.descricao} (${conteudo} ${item.unidade_embalagem || ''})`;
  }
}
