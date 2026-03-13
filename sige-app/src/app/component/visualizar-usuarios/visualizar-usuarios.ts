import { Component, ElementRef, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { UsuarioService } from '../../service/usuario.service';
import { Usuario } from '../../model/usuario';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-visualizar-usuarios',
  imports: [CommonModule, FormsModule],
  templateUrl: './visualizar-usuarios.html',
  styleUrl: './visualizar-usuarios.scss',
})
export class VisualizarUsuarios {

  constructor(
    private router: Router,
    private usuarioService: UsuarioService,
  ) { }

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild('myInput') input!: ElementRef;

  usuarios: Usuario[] = [];
  registro: Usuario = <Usuario>{ papel: '' };
  mostrarSenha = false;
  mensagemBotao = "Adicionar Novo Usuario";

  ngOnInit() {
    this.getUsuarios();
  }

  ngAfterViewInit() {

    const modalElement = this.modal.nativeElement;

    modalElement.addEventListener('shown.bs.modal', () => {
      this.input.nativeElement.focus();
    });

  }

  getUsuarios() {
    this.usuarioService.get().subscribe(
      {
        next: (registro: Usuario[]) => {
          this.usuarios = registro;
        }
      }
    );
  }

  verificarPapel(papel: string): string {
    if (papel === 'ADMIN') {
      return 'Administrador';
    }
    return 'Tecnico';
  }

  verificarStatus(status: boolean): string {
    if (status) {
      return 'Ativo';
    }
    return 'Inativo';
  }

  classStatus(status: boolean): string {
    if (!status) {
      return "bg-danger text-white";
    }
    else {
      return "bg-success text-white";
    }
  }

  toggleSenha() {
    this.mostrarSenha = !this.mostrarSenha;
  }


  reiniciarRegistro(): void {
    this.registro = <Usuario>{ papel: '' };
    this.mensagemBotao = "Adicionar Novo Usuario";
  }

  carregarRegistro(usuario: Usuario): void {
    this.registro = { ...usuario };
        this.mensagemBotao = "Atualizar Usuario";

  }

  saveUsuario(): void {
    let mensagem = "";
    if (this.registro.id) {
      mensagem = 'Tem certeza que deseja atualizar este usuário?';
    }
    else {
      mensagem = 'Tem certeza que deseja salvar este usuário?';
    }
    const confirmar = confirm(mensagem);
    if (!confirmar) {
      return;
    }
    if(!this.registro.id) {
      this.usuarioService.save(this.registro).subscribe(
        {
          next: (registro: Usuario) => {
            window.location.reload();
          }
        }
      );
    }
    else{
      this.usuarioService.patch(this.registro.id, this.registro).subscribe(
        {
          next: (registro: Usuario) => {
            window.location.reload();
          }
        }
      );
    }
  }

  desativarAtivarUsuario(usuario: Usuario): void {
    let mensagem = "";
    if (usuario.is_active) {
      mensagem = 'Tem certeza que deseja desativar este usuário?';
    }
    else {
      mensagem = 'Tem certeza que deseja ativar este usuário?';
    }
    const confirmar = confirm(mensagem);
    if (!confirmar) {
      return;
    }
    usuario.is_active = !usuario.is_active;
    this.usuarioService.patch(usuario.id, usuario).subscribe(
      {
        next: (registro: Usuario) => {
          window.location.reload();
        }
      }
    );
  }
}
