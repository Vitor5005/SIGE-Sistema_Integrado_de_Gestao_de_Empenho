import { Component } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { LicitacaoService } from '../../service/licitacao.service';
import { Licitacao } from '../../model/licitacao';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-visualizar-licitacao',
  imports: [RouterLink, CommonModule],
  templateUrl: './visualizar-licitacao.html',
  styleUrl: './visualizar-licitacao.scss',
})
export class VisualizarLicitacao {

  constructor(
    private router: Router,
    private licitacaoService: LicitacaoService,
  ) {}

  licitacoes: Licitacao = {} as Licitacao; 

  enviarPara(rota: string) {
    this.router.navigate([rota]);
  }
}
