import { FiltroConfig } from './../../model/filtro-config';
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
  ) {}

  registro: Licitacao[] = [];

  filtros: FiltroConfig[] = [
  {
    campo: 'data_abertura',
    label: 'Data de abertura',
    tipo: 'date-range'
  }
];
  filtrosAtivos: any = {};

  ngOnInit() {
    this.get();
    this.filtrosAtivos = {};
  }

  get(termobusca?: string): void {
  const filtrosParaEnvio = { ...this.filtrosAtivos };

  if (termobusca) {
    filtrosParaEnvio['search'] = termobusca;
  }

  // Se filtrosParaEnvio estiver vazio, buscar todos os registros
  this.licitacaoService.getComFiltros(filtrosParaEnvio).subscribe({
    next: (resposta: Licitacao[]) => {
      this.registro = this.ordenarLicitacoes(resposta || []);
    },
  });
}

  getOrdenadoValidade(): void {
    this.licitacaoService.get().subscribe({
      next: (resposta: Array<Licitacao>) => {
        this.registro = this.ordenarLicitacoes(resposta);
      },
    });
  }

  enviarPara(rota: string, id: number): void {
    this.router.navigate([rota], { queryParams: { id } });
  }

  aplicarFiltros(filtrosAtivos: any) {
  this.filtrosAtivos = filtrosAtivos || {};
  this.get();
}

  verificarValidade(licitacao: Licitacao): string {
    const dataAtual = new Date();
    const dataAbertura = new Date(licitacao.data_abertura);
    const validade = licitacao.validade;
    const dataExpiracao = new Date(dataAbertura);
    dataExpiracao.setMonth(dataExpiracao.getMonth() + Number(validade));
    if (dataAtual > dataExpiracao) {
      return 'Expirado';
    } else {
      return 'Válido';
    }
  }

  classValidade(licitacao: Licitacao): string {
    if (this.verificarValidade(licitacao) === 'Expirado') {
      return 'bg-danger text-white';
    } else {
      return 'bg-success text-white';
    }
  }

  ordenarLicitacoes(licitacoes: Licitacao[]): Licitacao[] {
    const dataAtual = new Date();

    return licitacoes.sort((a, b) => {
      const dataAberturaA = new Date(a.data_abertura);
      const dataExpiracaoA = new Date(dataAberturaA);
      dataExpiracaoA.setMonth(dataExpiracaoA.getMonth() + Number(a.validade));
      const validaA = dataAtual <= dataExpiracaoA;

      const dataAberturaB = new Date(b.data_abertura);
      const dataExpiracaoB = new Date(dataAberturaB);
      dataExpiracaoB.setMonth(dataExpiracaoB.getMonth() + Number(b.validade));
      const validaB = dataAtual <= dataExpiracaoB;

      // válidas primeiro
      if (validaA && !validaB) return -1;
      if (!validaA && validaB) return 1;

      // ordenar por data (mais recente primeiro)
      return dataAberturaB.getTime() - dataAberturaA.getTime();
    });
  }
}
