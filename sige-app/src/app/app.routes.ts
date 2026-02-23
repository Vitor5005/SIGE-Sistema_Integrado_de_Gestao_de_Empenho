import { Routes } from '@angular/router';
import { AdicionarLicitacao } from './component/adicionar-licitacao/adicionar-licitacao';
import { VisualizarLicitacoes } from './component/visualizar-licitacoes/visualizar-licitacoes';

export const routes: Routes = [
  {
    path: 'adicionar-licitacao',
    component: AdicionarLicitacao
  },
  {
    path: 'visualizar-licitacoes',
    component: VisualizarLicitacoes
  }
];
