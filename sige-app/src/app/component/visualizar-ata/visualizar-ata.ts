import { Component } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

@Component({
  selector: 'app-visualizar-ata',
  imports: [RouterLink],
  templateUrl: './visualizar-ata.html',
  styleUrl: './visualizar-ata.scss',
})
export class VisualizarAta {

  constructor(private router: Router){}

  enviarPara(rota: string){
      this.router.navigate([rota]);
  }

}
