import { BotaoVoltar } from './../utils/botao-voltar/botao-voltar';
import { Component } from '@angular/core';
import { Router, RouterLink, Route, ActivatedRoute } from '@angular/router';
import { AtaService } from '../../service/ata.service';
import { Ata } from '../../model/ata';
import { Fornecedor } from '../../model/fornecedor';
import { DecimalPipe, JsonPipe } from '@angular/common';
import { Empenho } from '../../model/empenho';
import { ItemAta } from '../../model/itemAta';
import { ItemEmpenho } from '../../model/itemEmpenho';

@Component({
  selector: 'app-visualizar-ata',
  imports: [RouterLink, DecimalPipe, BotaoVoltar],
  templateUrl: './visualizar-ata.html',
  styleUrl: './visualizar-ata.scss',
})
export class VisualizarAta {

  constructor(
    private router: Router,
    private ataService: AtaService,
    private route: ActivatedRoute
  ) { }


  ngOnInit() {

    const id = this.route.snapshot.queryParamMap.get('id');

    if (id) {
      this.get(Number(id))
      this.getEmpenho(Number(id));
      this.getItens(Number(id));
    }
  }

  ata: Ata = <Ata>{};
  empenho: Empenho = <Empenho>{};
  itens: Array<ItemEmpenho> = [];
  validade: string = "";

  enviarPara(rota: string, id?: number) {
    if(id){
      this.router.navigate([rota], { queryParams: { id } });
    }
    else{
      this.router.navigate([rota]);
    }
  }

  get(id: number) {
    this.ataService.getById(id).subscribe({
      next: (resposta: Ata) => {
        this.ata = resposta;
        this.verificarValidade(this.ata);
      }
    })
  }

  getEmpenho(ataId: number): void {
    this.ataService.getEmpenho(ataId).subscribe({
      next: (resposta: Empenho) => {
        this.empenho = resposta;
      },
    });
  }

  getItens(ataId: number): void {
    this.ataService.getItens(ataId).subscribe({
      next: (resposta: ItemEmpenho[]) => {
        this.itens = resposta;
      },
    });
  }

  verificarValidade(ata: Ata): string {
    const dataAtual = new Date();
    const dataAbertura = new Date(ata.licitacao.data_abertura);
    const validade = ata.licitacao.validade;
    const dataExpiracao = new Date(dataAbertura);
    dataExpiracao.setMonth(dataExpiracao.getMonth() + Number(validade));
    if (dataAtual > dataExpiracao) {
      this.validade = "Expirado";
    } else {
      this.validade = "Válido";
    }
    return this.validade;
  }

  classValidade(ata: Ata): string {
    if (this.verificarValidade(ata) === "Válido"){
      return "span-validade-valido";
    }
    return "span-validade-expirado";
  }



}
