import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { form } from '@angular/forms/signals';
import { Licitacao } from '../../model/licitacao';
import { LicitacaoService } from '../../service/licitacao.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-adicionar-licitacao',
  imports: [FormsModule, CommonModule, FormsModule],
  templateUrl: './adicionar-licitacao.html',
  styleUrl: './adicionar-licitacao.scss',
})
export class AdicionarLicitacao {

  constructor(
    private licitacaoService: LicitacaoService,
    private router: Router
  ){}

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

  licitacao: Licitacao = <Licitacao>{};
  
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

    this.licitacao.data_abertura = new Date().toISOString().split('T')[0];
  }

  save(){
    this.licitacaoService.save(this.licitacao).subscribe({
      next: (licitacao: Licitacao) => {
        const id = licitacao.id;
        alert('Licitacao salva com sucesso!');
        this.router.navigate(['/visualizar-licitacao'], {queryParams: { id }});
      }
    });
  }
}
