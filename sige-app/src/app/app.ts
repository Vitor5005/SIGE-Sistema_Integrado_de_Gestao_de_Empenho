import { Component, signal } from '@angular/core';
import { NavigationStart, Router, RouterOutlet } from '@angular/router';
import { Cabecalho } from './component/utils/cabecalho/cabecalho';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Cabecalho],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  protected readonly title = signal('sige-app');


  constructor(private router: Router) {

    this.router.events.subscribe(event => {

      if (event instanceof NavigationStart) {
        this.fecharModal();
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
