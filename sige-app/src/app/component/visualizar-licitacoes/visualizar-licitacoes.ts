
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
  ) { }

  ngOnInit() {
    this.get();
  }

  registro: Licitacao[] = [];

  get(): void {
    this.licitacaoService.get().subscribe({
      next: (resposta: Array<Licitacao>) => {
        this.registro = resposta;
      }
    });
  };

  ver() {
    console.log(this.registro);
  }

  enviarPara(rota: string, id: number): void {
    this.router.navigate([rota], { queryParams: { id } });
  }

  verificarValidade(licitacao: Licitacao): string {
    const dataAtual = new Date();
    const dataAbertura = new Date(licitacao.data_abertura);
    const validade = licitacao.validade;
    const dataExpiracao = new Date(dataAbertura);
    dataExpiracao.setMonth(dataExpiracao.getMonth() + Number(validade));
    if (dataAtual > dataExpiracao) {
      return "Expirado";
    } else {
      return "Válido";
    }
  }

  classValidade(licitacao: Licitacao): string {
    if (this.verificarValidade(licitacao) === "Expirado") {
      return "bg-danger text-white";
    }
    else {
      return "bg-success text-white";
    }
  }


}
