import { DatePipe, DecimalPipe } from '@angular/common';
import { Component } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from "@angular/router";
import { PendenciaFornecedor } from '../../../model/pendencia_fornecedor';
import { Auth } from '../../../service/auth';
import { PendenciaFornecedorService } from '../../../service/pendencia-fornecedor.service';
import { Acao, Papel, pode, Recurso } from '../../../security/rbac';

type TokenPayload = {
  papel?: string;
  username?: string;
};

@Component({
  selector: 'app-cabecalho',
  imports: [RouterLink, RouterLinkActive, DatePipe, DecimalPipe],
  templateUrl: './cabecalho.html',
  styleUrl: './cabecalho.scss',
})
export class Cabecalho {
  readonly pode = pode;
  readonly Acao = Acao;
  readonly Recurso = Recurso;

  constructor(
    private router: Router,
    private auth: Auth,
    private pendenciaService: PendenciaFornecedorService,
  ) { }

  papel: string = "";
  usuario: string = "";

  pendencias: PendenciaFornecedor[] = [];
  totalPendencias = 0;
  erroPendencias = false;
  marcandoCiente: number | null = null;

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
    this.carregarPendencias();
  }

  carregarPendencias(): void {
    if (!pode(Recurso.PENDENCIA_FORNECEDOR, Acao.ALTERAR_STATUS)) {
      return;
    }

    this.pendenciaService.listar('ABERTA', 1, 5).subscribe({
      next: (resposta) => {
        this.pendencias = resposta.results;
        this.totalPendencias = resposta.count;
        this.erroPendencias = false;
      },
      error: () => {
        this.erroPendencias = true;
      },
    });
  }

  marcarCiente(pendencia: PendenciaFornecedor): void {
    this.marcandoCiente = pendencia.id;
    this.pendenciaService.marcarCiente(pendencia.id).subscribe({
      next: () => {
        this.marcandoCiente = null;
        this.carregarPendencias();
      },
      error: () => {
        this.marcandoCiente = null;
        this.erroPendencias = true;
      },
    });
  }

  verificarPapel(papel: string): string {
    if (papel === Papel.DIRETOR) {
      return 'Diretor';
    }
    if (papel === Papel.NUTRICIONISTA) {
      return 'Nutricionista';
    }
    if (papel === Papel.ESTOQUISTA) {
      return 'Estoquista';
    }
    return 'Técnico Administrativo';
  }

  isGrupoAtivo(rotas: readonly string[]): boolean {
    const caminhoAtual = this.router.url.split(/[?#]/)[0];

    return rotas.some(
      rota => caminhoAtual === rota || caminhoAtual.startsWith(`${rota}/`)
    );
  }

}

