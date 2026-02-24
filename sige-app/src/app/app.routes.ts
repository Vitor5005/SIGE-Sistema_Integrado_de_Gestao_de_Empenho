import { Routes } from '@angular/router';
import { AdicionarLicitacao } from './component/adicionar-licitacao/adicionar-licitacao';
import { VisualizarLicitacoes } from './component/visualizar-licitacoes/visualizar-licitacoes';
import { VisualizarLicitacao } from './component/visualizar-licitacao/visualizar-licitacao';
import { VisualizarAtas } from './component/visualizar-atas/visualizar-atas';
import { VisualizarAta } from './component/visualizar-ata/visualizar-ata';
import { VisualizarEmpenhos } from './component/visualizar-empenhos/visualizar-empenhos';
import { VisualizarEmpenho } from './component/visualizar-empenho/visualizar-empenho';

export const routes: Routes = [
  {
    path: '',
    component: VisualizarLicitacoes
  },
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
  },
  {
    path: "visualizar-atas",
    component: VisualizarAtas
  },
  {
    path: 'visualizar-ata',
    component: VisualizarAta
  },
  {
    path: 'visualizar-empenhos',
    component: VisualizarEmpenhos
  },
  {
    path: "visualizar-empenho",
    component: VisualizarEmpenho
  }
];
