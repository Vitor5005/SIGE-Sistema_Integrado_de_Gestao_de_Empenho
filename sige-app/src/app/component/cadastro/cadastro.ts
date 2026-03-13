import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { UsuarioService } from '../../service/usuario.service';
import { Usuario } from '../../model/usuario';

@Component({
  selector: 'app-cadastro',
  imports: [RouterLink, CommonModule, FormsModule],
  templateUrl: './cadastro.html',
  styleUrl: './cadastro.scss',
})
export class Cadastro {

  constructor(
    private routerLink: Router,
    private usuarioService: UsuarioService
  ) {}

  mostrarSenha = false;
  mostrarConfirmar = false;
  registro: Usuario = <Usuario>{};

  toggleSenha() {
    this.mostrarSenha = !this.mostrarSenha;
  }

  toggleSenhaConfirmar(){
    this.mostrarConfirmar = !this.mostrarConfirmar;
  }

  cadastrarUsuario(){
    this.usuarioService.save(this.registro).subscribe({
      next: (response) => {
        alert('Usuário cadastrado com sucesso!');
        this.routerLink.navigate(['/login']);
      },
      error: (error) => {
        console.error('Erro ao cadastrar usuário:', error);
        alert('Ocorreu um erro ao cadastrar o usuário. Por favor, tente novamente.');
      }
    });
  }
}
