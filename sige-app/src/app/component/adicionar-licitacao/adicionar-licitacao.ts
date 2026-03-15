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
  formSubmitted: boolean = false;
  isSaving: boolean = false;
  errorMessage: string = '';

  get todayDate(): string {
    return new Date().toISOString().split('T')[0];
  }

  get numeroLicitacaoValido(): boolean {
    return Boolean(this.licitacao.numero_licitacao?.trim());
  }

  get validadeValida(): boolean {
    const validade = Number(this.licitacao.validade);
    return Number.isInteger(validade) && validade > 0 && validade <= 120;
  }

  get dataAberturaValida(): boolean {
    const data = this.licitacao.data_abertura;
    if (!data) {
      return false;
    }

    const hoje = new Date(this.todayDate + 'T00:00:00');
    const dataInformada = new Date(data + 'T00:00:00');
    return dataInformada <= hoje;
  }

  get podeCriarLicitacao(): boolean {
    return (
      !this.isSaving &&
      this.numeroLicitacaoValido &&
      this.validadeValida &&
      this.dataAberturaValida
    );
  }
  
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

  normalizarCampos(): void {
    this.licitacao.numero_licitacao = this.licitacao.numero_licitacao?.trim().toUpperCase();
    this.licitacao.validade = String(Number(this.licitacao.validade));
    this.licitacao.descricao = this.licitacao.descricao?.trim();
  }

  save(event?: Event){
    event?.preventDefault();
    this.formSubmitted = true;
    this.errorMessage = '';

    if (!this.podeCriarLicitacao) {
      return;
    }

    this.normalizarCampos();
    this.isSaving = true;

    this.licitacaoService.save(this.licitacao).subscribe({
      next: (licitacao: Licitacao) => {
        const id = licitacao.id;
        alert('Licitacao salva com sucesso!');
        this.router.navigate(['/visualizar-licitacao'], {queryParams: { id }});
      },
      error: () => {
        this.errorMessage = 'Não foi possível salvar a licitação. Revise os campos e tente novamente.';
        this.isSaving = false;
      }
    });
  }
}
