import { Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Router } from '@angular/router';
import { AtaService } from '../../service/ata.service';
import { Ata } from '../../model/ata';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-visualizar-atas',
  imports: [BarraPesquisa, CommonModule],
  templateUrl: './visualizar-atas.html',
  styleUrl: './visualizar-atas.scss',
})
export class VisualizarAtas {

  constructor(
    private router: Router,
    private ataService: AtaService
  ) { }

  atas = Array<Ata>();

  ngOnInit() {
    this.getOrdenadoValidade();
  }

  enviarPara(rota: string, id: number): void {
    this.router.navigate([rota], { queryParams: { id } });
  }

  get(termobusca?: string): void {
    this.ataService.get(termobusca).subscribe({
      next: (resposta: Array<Ata>) => {
        this.atas = resposta;
      }
    });
  }

  getOrdenadoValidade(termobusca?: string): void {
    this.ataService.get(termobusca).subscribe({
      next: (resposta: Array<Ata>) => {
        this.atas = this.ordenarAtas(resposta);
      }
    });
  }

  verificarValidade(ata: Ata): string {
    const dataAtual = new Date();
    const dataAbertura = new Date(ata.licitacao.data_abertura);
    const validade = ata.licitacao.validade;
    const dataExpiracao = new Date(dataAbertura);
    dataExpiracao.setMonth(dataExpiracao.getMonth() + Number(validade));
    if (dataAtual > dataExpiracao) {
      return "Expirado";
    } else {
      return "Válido";
    }
  }

  classValidade(ata: Ata): string {
    if (this.verificarValidade(ata) === "Expirado") {
      return "bg-danger text-white";
    }
    else {
      return "bg-success text-white";
    }
  }

  ordenarAtas(licitacoes: Ata[]): Ata[] {
    const dataAtual = new Date();

    return licitacoes.sort((a, b) => {

      const dataAberturaA = new Date(a.licitacao.data_abertura);
      const dataExpiracaoA = new Date(dataAberturaA);
      dataExpiracaoA.setMonth(dataExpiracaoA.getMonth() + Number(a.licitacao.validade));
      const validaA = dataAtual <= dataExpiracaoA;

      const dataAberturaB = new Date(b.licitacao.data_abertura);
      const dataExpiracaoB = new Date(dataAberturaB);
      dataExpiracaoB.setMonth(dataExpiracaoB.getMonth() + Number(b.licitacao.validade));
      const validaB = dataAtual <= dataExpiracaoB;

      // válidas primeiro
      if (validaA && !validaB) return -1;
      if (!validaA && validaB) return 1;

      // ordenar por data (mais recente primeiro)
      return dataAberturaB.getTime() - dataAberturaA.getTime();
    });
  }


}
