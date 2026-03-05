import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from "@angular/router";

@Component({
  selector: 'app-login',
  imports: [RouterLink, CommonModule],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login {

  mostrarSenha = false;

  toggleSenha() {
    this.mostrarSenha = !this.mostrarSenha;
  }

}
