import { Component, ElementRef, ViewChild } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FornecedorService } from '../../service/fornecedor.service';
import { Fornecedor } from '../../model/fornecedor';

@Component({
  selector: 'app-visualizar-fornecedor',
  imports: [RouterLink],
  templateUrl: './visualizar-fornecedor.html',
  styleUrl: './visualizar-fornecedor.scss',
})
export class VisualizarFornecedor {

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild("myInput") input!: ElementRef;

  constructor(
    private fornecedorService: FornecedorService
  ) {}

  fornecedor = <Fornecedor>{};

  ngOnInit(){

  }

  ngAfterViewInit() {

    const modalElement = this.modal.nativeElement;

    modalElement.addEventListener('shown.bs.modal', () => {

      console.log(this.input.nativeElement);
      this.input.nativeElement.focus();

    });

  }

}
