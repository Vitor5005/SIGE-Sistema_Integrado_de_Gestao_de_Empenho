import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-cadastro',
  imports: [RouterLink, CommonModule],
  templateUrl: './cadastro.html',
  styleUrl: './cadastro.scss',
})
export class Cadastro {
  mostrarSenha = false;
  mostrarConfirmar = false;

  toggleSenha() {
    this.mostrarSenha = !this.mostrarSenha;
  }
  toggleSenhaConfirmar(){
    this.mostrarConfirmar = !this.mostrarConfirmar;
  }
}
