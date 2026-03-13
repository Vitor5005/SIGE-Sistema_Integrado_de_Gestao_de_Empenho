import { Component } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from "@angular/router";
import { Auth } from '../../../service/auth';
import { UpperCasePipe } from '@angular/common';

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

  realizarLogout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  getPayload(): any | null {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    try {
      return JSON.parse(atob(token.split('.')[1]));
    } catch {
      return null;
    }
  }

  getPapel(): void {
    this.papel = this.getPayload()?.papel ?? null;
  }

  getUser(): void {
    this.usuario = this.getPayload()?.username ?? null;
  }


  ngOnInit() {
    this.getPapel();
    this.getUser();
  }

  verificarPapel(papel: string): string {
    if (papel === 'ADMIN') {
      return 'Administrador';
    }
    return 'Tecnico';
  }

}

