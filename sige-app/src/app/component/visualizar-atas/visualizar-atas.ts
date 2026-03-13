import { FiltroConfig } from './../../model/filtro-config';
import { Component } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Router } from '@angular/router';
import { AtaService } from '../../service/ata.service';
import { Ata } from '../../model/ata';
import { CommonModule } from '@angular/common';
import { map } from 'rxjs';

@Component({
  selector: 'app-visualizar-atas',
  imports: [BarraPesquisa, CommonModule],
  templateUrl: './visualizar-atas.html',
  styleUrl: './visualizar-atas.scss',
})
export class VisualizarAtas {
  constructor(private router: Router, private ataService: AtaService,
  ) {}

  atas: Ata[] = [];

  filtros: FiltroConfig[] = [
    {
      campo: 'licitacao__id',
      label: 'Licitação',
      tipo: 'checkbox',
      opcoes: [],
    },
    {
      campo: 'ata_saldo_total',
      label: 'Preço',
      tipo: 'range',
    },
    {
      campo: 'status',
      label: 'Status',
      tipo: 'radio',
      opcoes: [
        { valor: 'Válido', label: 'Válido' },
        { valor: 'Expirado', label: 'Expirado' },
      ],
    },
  ];

  filtrosAtivos: any = {};

  ngOnInit() {
    this.get();
    this.carregarLicitacoes();
  }

  enviarPara(rota: string, id: number): void {
    this.router.navigate([rota], { queryParams: { id } });
  }

  aplicarFiltros(filtros: any) {
    this.filtrosAtivos = filtros;
    this.get();
  }

  get(termobusca?: string): void {
    let params: any = { ...this.filtrosAtivos };
    if (termobusca) {
      params.search = termobusca;
    }

    this.ataService.get(params).subscribe({
      next: (resposta: Ata[]) => {
        let lista = this.ordenarAtas(resposta);

        if (params.status) {
          lista = lista.filter((a) => this.verificarValidade(a) === params.status);
        }
        this.atas = lista;
      },
    });
  }

  carregarLicitacoes() {
    this.ataService.get().subscribe({
      next: (atas) => {
        const mapa = new Map();

        atas.forEach((ata) => {
          mapa.set(ata.licitacao.id, {
            id: ata.licitacao.id,
            numero: ata.licitacao.numero_licitacao,
          });
        });

        this.filtros[0].opcoes = Array.from(mapa.values());
      },
    });
  }

  verificarValidade(ata: Ata): string {
    const dataAtual = new Date();
    const dataAbertura = new Date(ata.licitacao.data_abertura);
    const validade = ata.licitacao.validade;

    const dataExpiracao = new Date(dataAbertura);
    dataExpiracao.setMonth(dataExpiracao.getMonth() + Number(validade));

    return dataAtual > dataExpiracao ? 'Expirado' : 'Válido';
  }

  classValidade(ata: Ata): string {
    return this.verificarValidade(ata) === 'Expirado'
      ? 'bg-danger text-white'
      : 'bg-success text-white';
  }

  ordenarAtas(licitacoes: Ata[]): Ata[] {
    const dataAtual = new Date();

    return licitacoes.sort((a, b) => {
      const dataA = new Date(a.licitacao.data_abertura);
      const dataExpA = new Date(dataA);
      dataExpA.setMonth(dataExpA.getMonth() + Number(a.licitacao.validade));

      const dataB = new Date(b.licitacao.data_abertura);
      const dataExpB = new Date(dataB);
      dataExpB.setMonth(dataExpB.getMonth() + Number(b.licitacao.validade));

      const validaA = dataAtual <= dataExpA;
      const validaB = dataAtual <= dataExpB;

      if (validaA && !validaB) return -1;
      if (!validaA && validaB) return 1;

      return dataB.getTime() - dataA.getTime();
    });
  }
}
