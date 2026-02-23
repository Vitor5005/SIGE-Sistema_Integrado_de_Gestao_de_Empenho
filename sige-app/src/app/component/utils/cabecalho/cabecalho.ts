import { Component } from '@angular/core';
import { RouterLink } from "@angular/router";

@Component({
  selector: 'app-cabecalho',
  imports: [RouterLink],
  templateUrl: './cabecalho.html',
  styleUrl: './cabecalho.scss',
})
export class Cabecalho {

  ngOnInit(): void {
    const botoes = document.querySelectorAll("a.botao");
    botoes.forEach(botao => {
      botao.addEventListener('click', () => {
        const selecionado = document.querySelector("a.botao.selecionado");
        if (selecionado) {
          selecionado.classList.remove("selecionado");
        }
        botao.classList.add("selecionado");
      });
    });

  }





}

