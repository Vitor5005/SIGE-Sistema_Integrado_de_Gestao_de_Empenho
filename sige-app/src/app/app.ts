import { Component, DoCheck, signal } from '@angular/core';
import { NavigationEnd, NavigationStart, Router, RouterOutlet } from '@angular/router';
import { Cabecalho } from './component/utils/cabecalho/cabecalho';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Cabecalho, CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  mostrarLayout = true;
  protected readonly title = signal('sige-app');

  constructor(private router: Router) {

    this.router.events.subscribe(event => {

      if (event instanceof NavigationStart) {
        this.fecharModal();
      }

      if (event instanceof NavigationEnd) {
      const rota = event.urlAfterRedirects;

      const rotasSemLayout = ['/login', '/cadastrar-se'];

      this.mostrarLayout = !rotasSemLayout.some(r =>
        rota.startsWith(r)
      );
    }

    });

  }

  fecharModal() {

    document.body.classList.remove('modal-open');

    const backdrops =
      document.getElementsByClassName('modal-backdrop');

    while (backdrops.length > 0) {
      backdrops[0].remove();
    }
  }
}
