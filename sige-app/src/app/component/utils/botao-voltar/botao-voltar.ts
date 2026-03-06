import { Component } from '@angular/core';

@Component({
  selector: 'app-botao-voltar',
  imports: [],
  templateUrl: './botao-voltar.html',
  styleUrl: './botao-voltar.scss',
})
export class BotaoVoltar {
  voltar(){
    window.history.back()
  }
}
