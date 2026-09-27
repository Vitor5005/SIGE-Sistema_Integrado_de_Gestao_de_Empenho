import { Routes } from '@angular/router';
import { AdicionarLicitacao } from './component/adicionar-licitacao/adicionar-licitacao';
import { VisualizarLicitacoes } from './component/visualizar-licitacoes/visualizar-licitacoes';
import { VisualizarLicitacao } from './component/visualizar-licitacao/visualizar-licitacao';
import { VisualizarAtas } from './component/visualizar-atas/visualizar-atas';
import { VisualizarAta } from './component/visualizar-ata/visualizar-ata';
import { VisualizarEmpenhos } from './component/visualizar-empenhos/visualizar-empenhos';
import { VisualizarEmpenho } from './component/visualizar-empenho/visualizar-empenho';
import { VisualizarEntregas } from './component/visualizar-entregas/visualizar-entregas';
import { VisualizarFornecedores } from './component/visualizar-fornecedores/visualizar-fornecedores';
import { VisualizarFornecedor } from './component/visualizar-fornecedor/visualizar-fornecedor';
import { VisualizarGensAlimenticios } from './component/visualizar-gens-alimenticios/visualizar-gens-alimenticios';
import { Login } from './component/login/login';
import { Cadastro } from './component/cadastro/cadastro';
import { VisualizarGenAlimenticio } from './component/visualizar-gen-alimenticio/visualizar-gen-alimenticio';
import { RecuperarSenha } from './component/recuperar-senha/recuperar-senha';
import { authGuard } from './guard/auth.guard';
import { Home } from './component/home/home';
import { VisualizarUsuarios } from './component/visualizar-usuarios/visualizar-usuarios';
import { permissionGuard } from './guard/permission.guard';
import { Acao, Recurso } from './security/rbac';
import { Estoque } from './component/estoque/estoque';
import { ExtratoEstoque } from './component/estoque/extrato-estoque/extrato-estoque';
import { MovimentarEstoque } from './component/estoque/movimentar-estoque/movimentar-estoque';
import { RegistrarRecebimento } from './component/estoque/registrar-recebimento/registrar-recebimento';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },
  {
    path: 'login',
    component: Login
  },
  {
    path: 'recuperar-senha',
    component: RecuperarSenha
  },
  {
    path: "",
    canActivate: [authGuard],
    children: [
      {
        path: 'home',
        component: Home,
      },
      {
        path: 'visualizar-licitacoes',
        component: VisualizarLicitacoes,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.LICITACAO, acao: Acao.CONSULTAR } },
      },
      {
        path: 'adicionar-licitacao',
        component: AdicionarLicitacao,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.LICITACAO, acao: Acao.CADASTRAR } },
      },
      {
        path: 'visualizar-licitacao',
        component: VisualizarLicitacao,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.LICITACAO, acao: Acao.CONSULTAR } },
      },
      {
        path: "visualizar-atas",
        component: VisualizarAtas,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.ATA, acao: Acao.CONSULTAR } },
      },
      {
        path: 'visualizar-ata',
        component: VisualizarAta,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.ATA, acao: Acao.CONSULTAR } },
      },
      {
        path: 'visualizar-empenhos',
        component: VisualizarEmpenhos,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.EMPENHO, acao: Acao.CONSULTAR } },
      },
      {
        path: "visualizar-empenho",
        component: VisualizarEmpenho,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.EMPENHO, acao: Acao.CONSULTAR } },
      },
      {
        path: "visualizar-entregas",
        component: VisualizarEntregas,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.ORDEM_ENTREGA, acao: Acao.CONSULTAR } },
      },
      {
        path: "visualizar-fornecedores",
        component: VisualizarFornecedores,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.FORNECEDOR, acao: Acao.CONSULTAR } },
      },
      {
        path: "visualizar-fornecedor",
        component: VisualizarFornecedor,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.FORNECEDOR, acao: Acao.CONSULTAR } },
      },

      {
        path: "visualizar-gens-alimenticios",
        component: VisualizarGensAlimenticios,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.GENERO_ALIMENTICIO, acao: Acao.CONSULTAR } },
      },
      {
        path: 'visualizar-gen-alimenticio',
        component: VisualizarGenAlimenticio,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.GENERO_ALIMENTICIO, acao: Acao.CONSULTAR } },
      },
      {
        path: 'estoque',
        component: Estoque,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.ESTOQUE, acao: Acao.CONSULTAR } },
      },
      {
        path: 'estoque/extrato',
        component: ExtratoEstoque,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.MOVIMENTACAO_ESTOQUE, acao: Acao.CONSULTAR_EXTRATO } },
      },
      {
        path: 'estoque/movimentacao',
        component: MovimentarEstoque,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.ESTOQUE, acao: Acao.REGISTRAR_SAIDA } },
      },
      {
        path: 'estoque/recebimento',
        component: RegistrarRecebimento,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.ESTOQUE, acao: Acao.REGISTRAR_RECEBIMENTO } },
      }
    ]
  },
  {
    path: "",
    canActivate: [authGuard],
    children: [
      {
        path: "visualizar-usuarios",
        component: VisualizarUsuarios,
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.USUARIO, acao: Acao.CONSULTAR } },
      }
    ]
  },
  {
    path: '**',
    redirectTo: 'home'
  }

];
