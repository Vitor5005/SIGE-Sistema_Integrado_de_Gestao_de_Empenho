import { Component, ElementRef, ViewChild } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-visualizar-fornecedor',
  imports: [RouterLink],
  templateUrl: './visualizar-fornecedor.html',
  styleUrl: './visualizar-fornecedor.scss',
})
export class VisualizarFornecedor {

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild("myInput") input!: ElementRef;

  ngAfterViewInit() {

    const modalElement = this.modal.nativeElement;

    modalElement.addEventListener('shown.bs.modal', () => {

      console.log(this.input.nativeElement);
      this.input.nativeElement.focus();

    });

  }

}
