import { DatePipe, UpperCasePipe } from '@angular/common';
import { Component, ElementRef, HostListener, Input, ViewChild } from '@angular/core';

import { Cardapio, ItemCardapio } from '../../../model/cardapio';
import { agruparPorSecao, formatarQuantidade } from '../cardapio-util';

/** Folha A4 em px CSS (96 px por polegada). */
const MM = 96 / 25.4;
const LARGURA_A4 = 210 * MM;
// Um pouco abaixo dos 297 mm: arredondamentos do navegador não podem empurrar nada para uma 2ª página.
const ALTURA_UTIL_A4 = 293 * MM;

/** Cardápio quantitativo no mesmo modelo da folha impressa usada pelo Restaurante Universitário. */
@Component({
  selector: 'app-cardapio-documento',
  imports: [DatePipe, UpperCasePipe],
  templateUrl: './cardapio-documento.html',
  styleUrl: './cardapio-documento.scss',
})
export class CardapioDocumento {
  @Input({ required: true }) cardapio!: Cardapio;

  @ViewChild('documento', { static: true }) private documento!: ElementRef<HTMLElement>;

  /**
   * O PDF tem de caber em uma única página. Antes de imprimir, aplica o layout compacto
   * de impressão, mede a altura e, se ainda passar de uma folha A4, reduz tudo (zoom)
   * na proporção necessária, alargando a área para que a largura continue a da folha.
   */
  @HostListener('window:beforeprint')
  ajustarParaUmaPagina(): void {
    const elemento = this.documento.nativeElement;
    elemento.classList.add('documento--impressao');
    elemento.style.removeProperty('zoom');
    elemento.style.width = `${LARGURA_A4}px`;

    const escala = Math.min(1, ALTURA_UTIL_A4 / elemento.scrollHeight);
    if (escala < 1) {
      elemento.style.width = `${LARGURA_A4 / escala}px`;
      // A altura muda com a nova largura (menos quebras de linha); mede de novo.
      const escalaFinal = Math.min(1, ALTURA_UTIL_A4 / elemento.scrollHeight);
      elemento.style.width = `${LARGURA_A4 / escalaFinal}px`;
      elemento.style.setProperty('zoom', String(escalaFinal));
    }
  }

  @HostListener('window:afterprint')
  restaurarDepoisDaImpressao(): void {
    const elemento = this.documento.nativeElement;
    elemento.classList.remove('documento--impressao');
    elemento.style.removeProperty('zoom');
    elemento.style.removeProperty('width');
  }

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
