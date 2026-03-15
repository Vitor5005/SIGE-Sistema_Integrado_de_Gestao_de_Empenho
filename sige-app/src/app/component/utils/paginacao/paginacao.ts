import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-paginacao',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './paginacao.html',
  styleUrl: './paginacao.scss',
})
export class Paginacao {
  @Input() currentPage: number = 1;
  @Input() pageSize: number = 5;
  @Input() totalItems: number = 0;
  @Input() totalLabel: string = 'Total de registros';
  @Input() showTotal: boolean = true;

  @Output() pageChange = new EventEmitter<number>();

  get totalPages(): number {
    return Math.ceil(this.totalItems / this.pageSize);
  }

  get visiblePages(): Array<number | string> {
    const totalPages = this.totalPages;

    if (totalPages <= 1) {
      return [1];
    }

    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, index) => index + 1);
    }

    const pages: Array<number | string> = [1];
    let start = Math.max(2, this.currentPage - 1);
    let end = Math.min(totalPages - 1, this.currentPage + 1);

    if (this.currentPage <= 3) {
      start = 2;
      end = 4;
    }

    if (this.currentPage >= totalPages - 2) {
      start = totalPages - 3;
      end = totalPages - 1;
    }

    if (start > 2) {
      pages.push('...');
    }

    for (let page = start; page <= end; page += 1) {
      pages.push(page);
    }

    if (end < totalPages - 1) {
      pages.push('...');
    }

    pages.push(totalPages);

    return pages;
  }

  irParaPagina(page: number): void {
    if (page < 1 || page > this.totalPages || page === this.currentPage) {
      return;
    }

    this.pageChange.emit(page);
  }

  paginaAnterior(): void {
    this.irParaPagina(this.currentPage - 1);
  }

  proximaPagina(): void {
    this.irParaPagina(this.currentPage + 1);
  }
}
