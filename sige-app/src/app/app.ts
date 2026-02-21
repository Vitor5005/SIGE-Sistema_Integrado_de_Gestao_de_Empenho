import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Cabecalho } from './component/utils/cabecalho/cabecalho';
import { AdicionarLicitacao } from './component/adicionar-licitacao/adicionar-licitacao';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Cabecalho, AdicionarLicitacao],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  protected readonly title = signal('sige-app');
}
