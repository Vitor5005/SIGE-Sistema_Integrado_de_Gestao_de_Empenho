import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from "@angular/router";

@Component({
  selector: 'app-cabecalho',
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './cabecalho.html',
  styleUrl: './cabecalho.scss',
})
export class Cabecalho {

  ngOnInit(): void {
    const botoes = document.querySelectorAll("a.botao");
    const urlAtual = window.location.pathname;

    botoes.forEach(botao => {
      const selecionado = document.querySelector("a.botao.selecionado");
      if(botao.getAttribute('RouterLink') === urlAtual){
          if (selecionado) {
          selecionado.classList.remove("selecionado");
        }
          botao.classList.add("selecionado");
        }
      botao.addEventListener('click', () => {
        if (selecionado) {
          selecionado.classList.remove("selecionado");
        }
        botao.classList.add("selecionado");
      });
    });

  }





}

