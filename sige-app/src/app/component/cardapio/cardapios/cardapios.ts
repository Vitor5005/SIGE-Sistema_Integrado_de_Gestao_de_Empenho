import { DatePipe } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { CardapioResumo, REFEICOES } from '../../../model/cardapio';
import { FiltroConfig } from '../../../model/filtro-config';
import { Acao, pode, Recurso } from '../../../security/rbac';
import { CardapioService } from '../../../service/cardapio.service';
import { BarraPesquisa } from '../../utils/barra-pesquisa/barra-pesquisa';
import { EstadoConteudo } from '../../utils/estado-conteudo/estado-conteudo';
import { Paginacao } from '../../utils/paginacao/paginacao';
import { classeStatusCardapio } from '../cardapio-util';

@Component({
  selector: 'app-cardapios',
  imports: [BarraPesquisa, DatePipe, EstadoConteudo, Paginacao, RouterLink],
  templateUrl: './cardapios.html',
  styleUrl: './cardapios.scss',
})
export class Cardapios implements OnInit {
  readonly pode = pode;
  readonly Acao = Acao;
  readonly Recurso = Recurso;
  readonly classeStatus = classeStatusCardapio;

  filtros: FiltroConfig[] = [
    {
      campo: 'status',
      label: 'Situação',
      tipo: 'select',
      opcoes: [
        { valor: 'RASCUNHO', label: 'Rascunho' },
        { valor: 'ENVIADO', label: 'Aguardando aprovação do estoque' },
        { valor: 'RECUSADO', label: 'Recusado pelo estoque' },
        { valor: 'APROVADO', label: 'Retirada aprovada' },
        { valor: 'CONSUMO_INFORMADO', label: 'Consumo aguardando confirmação' },
        { valor: 'FINALIZADO', label: 'Finalizado' },
        { valor: 'ALTERACAO_SOLICITADA', label: 'Alteração aguardando o estoque' },
        { valor: 'SUBSTITUIDO', label: 'Substituído por alteração' },
      ],
    },
    {
      campo: 'refeicao',
      label: 'Refeição',
      tipo: 'select',
      opcoes: REFEICOES.map(({ valor, label }) => ({ valor, label })),
    },
  ];

  cardapios: CardapioResumo[] = [];
  termoBusca = '';
  filtrosAtivos: Record<string, any> = {};
  currentPage = 1;
  pageSize = 10;
  total = 0;
  carregando = false;
  erro = '';

  constructor(private cardapioService: CardapioService, private router: Router) {}

  ngOnInit(): void {
    this.carregar();
  }

  carregar(termo?: string): void {
    if (termo !== undefined) {
      this.termoBusca = termo;
      this.currentPage = 1;
    }

    this.carregando = true;
    this.erro = '';
    this.cardapioService.listar({
      search: this.termoBusca,
      status: this.filtrosAtivos['status'] || '',
      refeicao: this.filtrosAtivos['refeicao'] || '',
    }, this.currentPage, this.pageSize).subscribe({
      next: (resposta) => {
        this.cardapios = resposta.results;
        this.total = resposta.count;
        this.carregando = false;
      },
      error: () => {
        this.erro = 'Não foi possível carregar os cardápios.';
        this.carregando = false;
      },
    });
  }

  aplicarFiltros(filtros: Record<string, any>): void {
    this.filtrosAtivos = { ...filtros };
    this.currentPage = 1;
    this.carregar();
  }

  irParaPagina(pagina: number): void {
    this.currentPage = pagina;
    this.carregar();
  }

  alterarPageSize(tamanho: number): void {
    this.pageSize = tamanho;
    this.currentPage = 1;
    this.carregar();
  }

  abrir(cardapio: CardapioResumo): void {
    this.router.navigate(['/cardapio'], { queryParams: { id: cardapio.id } });
  }
}
