import { Component } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LicitacaoService } from '../../service/licitacao.service';
import { Licitacao } from '../../model/licitacao';
import { CommonModule } from '@angular/common';
import { AtaService } from '../../service/ata.service';
import { Ata } from '../../model/ata';
import { BotaoVoltar } from "../utils/botao-voltar/botao-voltar";

@Component({
  selector: 'app-visualizar-licitacao',
  imports: [RouterLink, CommonModule, BotaoVoltar],
  templateUrl: './visualizar-licitacao.html',
  styleUrl: './visualizar-licitacao.scss',
})
export class VisualizarLicitacao {

  constructor(
    private router: Router,
    private licitacaoService: LicitacaoService,
    private ataService: AtaService,
    private route: ActivatedRoute
  ) {}

  licitacao: Licitacao = <Licitacao>{};
  atas: Array<Ata> = Array<Ata>();

  ngOnInit() {

    const id = this.route.snapshot.queryParamMap.get('id');

    if (id) {
      this.get(Number(id));
    }
  }

  enviarPara(rota: string, id?: number): void {
    if(id){
      this.router.navigate([rota], { queryParams: { id } });
    }
    else{
      this.router.navigate([rota]);
    }
  }

  get(id: number): void {
    this.licitacaoService.getById(id).subscribe({
      next: (resposta: Licitacao) => {
        this.licitacao = resposta;
      },
      complete: () => {
        this.getAtas(this.licitacao.id);
      }
    });
  }

  getAtas(licitacaoId: number): void {
    this.ataService.get(String(licitacaoId)).subscribe({
      next: (resposta: Array<Ata>) => {
        this.atas = resposta;
      }
    });
  }
}
