import { Component } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from "@angular/router";
import { Auth } from '../../../service/auth';

type TokenPayload = {
  papel?: string;
  username?: string;
};

@Component({
  selector: 'app-cabecalho',
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './cabecalho.html',
  styleUrl: './cabecalho.scss',
})
export class Cabecalho {

  constructor(
    private router: Router,
    private auth: Auth
  ) { }

  papel: string = "";
  usuario: string = "";

  readonly rotasAquisicoes = [
    '/visualizar-licitacoes',
    '/visualizar-licitacao',
    '/adicionar-licitacao',
    '/visualizar-atas',
    '/visualizar-ata',
    '/visualizar-empenhos',
    '/visualizar-empenho',
  ] as const;

  readonly rotasCadastros = [
    '/visualizar-fornecedores',
    '/visualizar-fornecedor',
    '/visualizar-gens-alimenticios',
    '/visualizar-gen-alimenticio',
  ] as const;

  realizarLogout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  getPayload(): TokenPayload | null {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    try {
      return JSON.parse(atob(token.split('.')[1])) as TokenPayload;
    } catch {
      return null;
    }
  }

  getPapel(): void {
    this.papel = this.getPayload()?.papel ?? '';
  }

  getUser(): void {
    this.usuario = this.getPayload()?.username ?? '';
  }


  ngOnInit() {
    this.getPapel();
    this.getUser();
  }

  verificarPapel(papel: string): string {
    if (papel === 'ADMIN') {
      return 'Administrador';
    }
    return 'Técnico';
  }

  isGrupoAtivo(rotas: readonly string[]): boolean {
    const caminhoAtual = this.router.url.split(/[?#]/)[0];

    return rotas.some(
      rota => caminhoAtual === rota || caminhoAtual.startsWith(`${rota}/`)
    );
  }

}

