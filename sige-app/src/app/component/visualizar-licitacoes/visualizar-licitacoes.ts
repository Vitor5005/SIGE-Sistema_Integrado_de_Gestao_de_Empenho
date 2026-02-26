import { ChangeDetectorRef, Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Router } from '@angular/router';
import { Licitacao } from '../../model/licitacao';
import { LicitacaoService } from '../../service/licitacao.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-licitacoes',
  imports: [BarraPesquisa, CommonModule],
  templateUrl: './visualizar-licitacoes.html',
  styleUrl: './visualizar-licitacoes.scss',
})
export class VisualizarLicitacoes {

  constructor(
    private router: Router,
    private licitacaoService: LicitacaoService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit() {
    this.get();
  }

  registro: Licitacao[] = [];

  get(): void {
    this.licitacaoService.get().subscribe({
      next: (resposta: Array<Licitacao>) => {
        this.registro = resposta;
        this.cdr.detectChanges();
      }
    });
  };

  ver(){
    console.log(this.registro);
  }

  enviarPara(rota: string) {
    this.router.navigate([rota]);
  }

}
