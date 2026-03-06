import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { FornecedorService } from '../../service/fornecedor.service';
import { Fornecedor } from '../../model/fornecedor';
import { CommonModule, JsonPipe } from '@angular/common';

@Component({
  selector: 'app-visualizar-fornecedores',
  imports: [CommonModule],
  templateUrl: './visualizar-fornecedores.html',
  styleUrl: './visualizar-fornecedores.scss',
})
export class VisualizarFornecedores {

  constructor(
    private router: Router,
    private fornecedorService: FornecedorService,
  ) { }

  fornecedores = Array<Fornecedor>()

  ngOnInit(){

    this.get()

  }

  enviarPara(rota: string, id?: number) {
    if (id) {
      this.router.navigate([rota], { queryParams: { id } });
    } else {
      this.router.navigate([rota]);
    }
  }

  get(termobusca?: string): void {
    this.fornecedorService.get(termobusca).subscribe(
      {
        next: (resposta: Array<Fornecedor>) => {
          this.fornecedores = resposta
        }
      }
    )
  }

}
