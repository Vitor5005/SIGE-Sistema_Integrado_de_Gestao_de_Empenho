import { Routes } from '@angular/router';
import { AdicionarLicitacao } from './component/adicionar-licitacao/adicionar-licitacao';
import { VisualizarLicitacoes } from './component/visualizar-licitacoes/visualizar-licitacoes';
import { VisualizarLicitacao } from './component/visualizar-licitacao/visualizar-licitacao';

export const routes: Routes = [
  {
    path: 'adicionar-licitacao',
    component: AdicionarLicitacao
  },
  {
    path: 'visualizar-licitacoes',
    component: VisualizarLicitacoes
  },
  {
    path: "visualizar-licitacao",
    component: VisualizarLicitacao
  }
];
