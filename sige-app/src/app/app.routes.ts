import { Routes } from '@angular/router';
import { AdicionarLicitacao } from './component/adicionar-licitacao/adicionar-licitacao';
import { Licitacoes } from './component/licitacoes/licitacoes';

export const routes: Routes = [
  {
    path: 'adicionar-licitacao',
    component: AdicionarLicitacao
  },
  {
    path: 'licitacoes',
    component: Licitacoes
  }
];
