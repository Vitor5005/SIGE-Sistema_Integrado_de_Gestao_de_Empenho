import { Injectable } from '@angular/core';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root',
})
export class Navegacao {
  
  constructor(private router: Router) {}

  enviarPara(rota: string){
    this.router.navigate([rota]);
  }

}
