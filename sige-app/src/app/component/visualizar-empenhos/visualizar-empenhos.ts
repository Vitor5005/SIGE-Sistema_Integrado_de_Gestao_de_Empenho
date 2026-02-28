import { Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Router } from '@angular/router';
import { EmpenhoService } from '../../service/empenho.service';
import { Empenho } from '../../model/empenho';

@Component({
  selector: 'app-visualizar-empenhos',
  imports: [BarraPesquisa],
  templateUrl: './visualizar-empenhos.html',
  styleUrl: './visualizar-empenhos.scss',
})
export class VisualizarEmpenhos {

  constructor(
    private router: Router,
    private empenhoService: EmpenhoService
  ){}

  empenhos = Array<Empenho>();

  ngOnInit() {
    this.get();
  }

  enviarPara(rota: string){
    this.router.navigate([rota]);
  }

  get(termobusca?: string): void {
    this.empenhoService.get(termobusca).subscribe({
      next: (resposta: Array<Empenho>) => {
        this.empenhos = resposta;
      }
    });
  }
}
