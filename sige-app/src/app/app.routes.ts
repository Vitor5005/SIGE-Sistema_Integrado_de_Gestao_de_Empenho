import { Routes } from '@angular/router';
import { Login } from './component/login/login';
import { authGuard } from './guard/auth.guard';
import { permissionGuard } from './guard/permission.guard';
import { Acao, Recurso } from './security/rbac';

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
    loadComponent: () => import('./component/recuperar-senha/recuperar-senha').then(m => m.RecuperarSenha)
  },
  {
    path: "",
    canActivate: [authGuard],
    children: [
      {
        path: 'home',
        loadComponent: () => import('./component/home/home').then(m => m.Home),
      },
      {
        path: 'visualizar-licitacoes',
        loadComponent: () => import('./component/visualizar-licitacoes/visualizar-licitacoes').then(m => m.VisualizarLicitacoes),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.LICITACAO, acao: Acao.CONSULTAR } },
      },
      {
        path: 'adicionar-licitacao',
        loadComponent: () => import('./component/adicionar-licitacao/adicionar-licitacao').then(m => m.AdicionarLicitacao),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.LICITACAO, acao: Acao.CADASTRAR } },
      },
      {
        path: 'visualizar-licitacao',
        loadComponent: () => import('./component/visualizar-licitacao/visualizar-licitacao').then(m => m.VisualizarLicitacao),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.LICITACAO, acao: Acao.CONSULTAR } },
      },
      {
        path: "visualizar-atas",
        loadComponent: () => import('./component/visualizar-atas/visualizar-atas').then(m => m.VisualizarAtas),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.ATA, acao: Acao.CONSULTAR } },
      },
      {
        path: 'visualizar-ata',
        loadComponent: () => import('./component/visualizar-ata/visualizar-ata').then(m => m.VisualizarAta),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.ATA, acao: Acao.CONSULTAR } },
      },
      {
        path: 'visualizar-empenhos',
        loadComponent: () => import('./component/visualizar-empenhos/visualizar-empenhos').then(m => m.VisualizarEmpenhos),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.EMPENHO, acao: Acao.CONSULTAR } },
      },
      {
        path: "visualizar-empenho",
        loadComponent: () => import('./component/visualizar-empenho/visualizar-empenho').then(m => m.VisualizarEmpenho),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.EMPENHO, acao: Acao.CONSULTAR } },
      },
      {
        path: "visualizar-entregas",
        loadComponent: () => import('./component/visualizar-entregas/visualizar-entregas').then(m => m.VisualizarEntregas),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.ORDEM_ENTREGA, acao: Acao.CONSULTAR } },
      },
      {
        path: "visualizar-fornecedores",
        loadComponent: () => import('./component/visualizar-fornecedores/visualizar-fornecedores').then(m => m.VisualizarFornecedores),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.FORNECEDOR, acao: Acao.CONSULTAR } },
      },
      {
        path: "visualizar-fornecedor",
        loadComponent: () => import('./component/visualizar-fornecedor/visualizar-fornecedor').then(m => m.VisualizarFornecedor),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.FORNECEDOR, acao: Acao.CONSULTAR } },
      },

      {
        path: "visualizar-gens-alimenticios",
        loadComponent: () => import('./component/visualizar-gens-alimenticios/visualizar-gens-alimenticios').then(m => m.VisualizarGensAlimenticios),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.GENERO_ALIMENTICIO, acao: Acao.CONSULTAR } },
      },
      {
        path: 'estoque',
        loadComponent: () => import('./component/estoque/estoque').then(m => m.Estoque),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.ESTOQUE, acao: Acao.CONSULTAR } },
      },
      {
        path: 'estoque/extrato',
        loadComponent: () => import('./component/estoque/extrato-estoque/extrato-estoque').then(m => m.ExtratoEstoque),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.MOVIMENTACAO_ESTOQUE, acao: Acao.CONSULTAR_EXTRATO } },
      },
      {
        path: 'estoque/movimentacao',
        loadComponent: () => import('./component/estoque/movimentar-estoque/movimentar-estoque').then(m => m.MovimentarEstoque),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.ESTOQUE, acao: Acao.REGISTRAR_SAIDA } },
      },
      {
        path: 'estoque/recebimento',
        loadComponent: () => import('./component/estoque/registrar-recebimento/registrar-recebimento').then(m => m.RegistrarRecebimento),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.ESTOQUE, acao: Acao.REGISTRAR_RECEBIMENTO } },
      },
      {
        path: 'cardapios',
        loadComponent: () => import('./component/cardapio/cardapios/cardapios').then(m => m.Cardapios),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.CARDAPIO, acao: Acao.CONSULTAR } },
      },
      {
        path: 'cardapios/novo',
        loadComponent: () => import('./component/cardapio/cardapio-form/cardapio-form').then(m => m.CardapioForm),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.CARDAPIO, acao: Acao.CADASTRAR } },
      },
      {
        path: 'cardapios/editar',
        loadComponent: () => import('./component/cardapio/cardapio-form/cardapio-form').then(m => m.CardapioForm),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.CARDAPIO, acao: Acao.EDITAR } },
      },
      {
        path: 'cardapio',
        loadComponent: () => import('./component/cardapio/cardapio-detalhe/cardapio-detalhe').then(m => m.CardapioDetalhe),
        canActivate: [permissionGuard],
        data: { permission: { recurso: Recurso.CARDAPIO, acao: Acao.CONSULTAR } },
      }
    ]
  },
  {
    path: "",
    canActivate: [authGuard],
    children: [
      {
        path: "visualizar-usuarios",
        loadComponent: () => import('./component/visualizar-usuarios/visualizar-usuarios').then(m => m.VisualizarUsuarios),
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
