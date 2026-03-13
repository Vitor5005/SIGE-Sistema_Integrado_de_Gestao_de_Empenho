import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { Router, RouterLink } from "@angular/router";
import { Auth } from '../../service/auth';
import { FormsModule } from '@angular/forms';
import { Token } from '../../model/token';

@Component({
  selector: 'app-login',
  imports: [RouterLink, CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login {

  constructor(
    private router: Router,
    private auth: Auth
  ){}

  mostrarSenha = false;

  username = "";
  password = "";
  
  toggleSenha() {
    this.mostrarSenha = !this.mostrarSenha;
  }

  realizarLogin() {
    this.auth.login(this.username, this.password).subscribe({
      next: (resposta: Token) => {
        this.auth.salvarToken(resposta.access, resposta.refresh);
        this.router.navigate(['/home']);
      },
      error: (erro) => {
        alert("Erro ao realizar login. Verifique suas credenciais.");
      }
    });
  }


}
