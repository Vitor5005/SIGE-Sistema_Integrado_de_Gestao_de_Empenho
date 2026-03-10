import { Component } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from "@angular/router";
import { Auth } from '../../../service/auth';

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

  realizarLogout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }


  ngOnInit() {

  }





}

