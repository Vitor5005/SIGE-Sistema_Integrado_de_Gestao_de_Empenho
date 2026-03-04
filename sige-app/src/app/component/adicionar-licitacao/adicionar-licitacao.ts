import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { form } from '@angular/forms/signals';

@Component({
  selector: 'app-adicionar-licitacao',
  imports: [FormsModule, CommonModule],
  templateUrl: './adicionar-licitacao.html',
  styleUrl: './adicionar-licitacao.scss',
})
export class AdicionarLicitacao {
  form = {
    catmat: '',
    qtdLicitada: '',
    valorUnitario: '',
    marca: '',
    categoria: '',
    unidadeMedida: '',
    descricao: '',
    valorTotal: ''
  };
  lista: any[] = [];
  adicionar(){
    this.lista.push({... this.form});
    this.form = {
    catmat: '',
    qtdLicitada: '',
    valorUnitario: '',
    marca: '',
    categoria: '',
    unidadeMedida: '',
    descricao: '',
    valorTotal: ''};
  }
  excluirItem(index: number) {
  if (confirm('Deseja realmente excluir este item?')) {
    this.lista.splice(index, 1);
  }
}
  ngOnInit(): void {
    const submitbtn = document.querySelector('.btn-submit') as HTMLElement | null;
    const adicionados = document.querySelector('.itens-adicionados') as HTMLElement | null;
    console.log(adicionados)
    submitbtn?.addEventListener("click", ()=>{
      adicionados?.classList.remove('vazia')
    })

  }
}
