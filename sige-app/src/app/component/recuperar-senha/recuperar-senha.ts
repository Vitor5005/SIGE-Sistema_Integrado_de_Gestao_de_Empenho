import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, signal } from '@angular/core';
import { Router, RouterLink } from "@angular/router";
import { Auth } from '../../service/auth';
import { FormsModule } from '@angular/forms';
import { Token } from '../../model/token';

@Component({
  selector: 'app-recuperar-senha',
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './recuperar-senha.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  styleUrl: './recuperar-senha.scss',
})
export class RecuperarSenha {

  constructor(
    private authService: Auth,
    private router: Router
  ) { }

  mostrarSenha = false;
  mostrarConfirmar = false;
  etapa = signal<'email' | 'codigo' | 'nova_senha'>('email');
  email = "";
  ns = ["", "", "", "", "", ""]
  codigo = "";
  password = "";
  token: Token = <Token>{};

  toggleSenha() {
    this.mostrarSenha = !this.mostrarSenha;
  }

  toggleSenhaConfirmar() {
    this.mostrarConfirmar = !this.mostrarConfirmar;
  }

  // Muda para a tela de inserção de código
  irParaCodigo(): void {
    this.etapa.set('codigo');
  }


  irParaNovaSenha(): void {
    this.etapa.set('nova_senha');
  }

  // Ação final (apenas log para demonstração)
  finalizar(): void {
    console.log('Processo de verificação concluído.');
  }

  pedirEmail() {
    this.authService.passwordResetEmail(this.email).subscribe({
      complete: () => {
        this.irParaCodigo();
      }
    });
  }

  enviarCodigo() {
    this.codigo = this.ns.join('');
    this.authService.passwordResetCode(this.codigo).subscribe({
      next: (token) => {
        this.token = token;
      },
      complete: () => {
        this.irParaNovaSenha();
      }
    });
  }

  enviarNovaSenha() {
    this.authService.passwordResetPassword(this.token.reset_token, this.password).subscribe({
      complete: () => {
        this.router.navigate(['/login']);
      }
    });
  }

}
