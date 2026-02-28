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
  ) {}

  atas = Array<Ata>();

  ngOnInit() {
    this.get();
  }

  enviarPara(rota: string) {
    this.router.navigate([rota]);
  }

  get(termobusca?: string): void {
    this.ataService.get(termobusca).subscribe({
      next: (resposta: Array<Ata>) => {
        this.atas = resposta;
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
    if(this.verificarValidade(ata) === "Expirado") {
      return "bg-danger text-white";
    }
    else{
      return "bg-success text-white";
    }
  }

}
