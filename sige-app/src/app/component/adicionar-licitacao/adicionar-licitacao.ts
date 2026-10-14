import { CommonModule } from '@angular/common';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { form } from '@angular/forms/signals';
import { Licitacao } from '../../model/licitacao';
import { LicitacaoService } from '../../service/licitacao.service';
import { Router } from '@angular/router';
import { FeedbackService } from '../../service/feedback.service';

@Component({
  selector: 'app-adicionar-licitacao',
  imports: [FormsModule, CommonModule, FormsModule],
  templateUrl: './adicionar-licitacao.html',
  styleUrl: './adicionar-licitacao.scss',
})
export class AdicionarLicitacao {

  constructor(
    private licitacaoService: LicitacaoService,
    private router: Router,
    private feedback: FeedbackService
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

  @ViewChild('tituloRevisao') tituloRevisao?: ElementRef<HTMLElement>;

  licitacao: Licitacao = <Licitacao>{ atual: false };
  formSubmitted: boolean = false;
  emRevisao: boolean = false;
  isSaving: boolean = false;
  errorMessage: string = '';
  licitacaoAtual: Licitacao | null = null;
  carregandoLicitacaoAtual: boolean = true;
  erroAoCarregarLicitacaoAtual: boolean = false;
  private usuarioAlterouOpcaoAtual: boolean = false;

  get todayDate(): string {
    const hoje = new Date();
    const ano = hoje.getFullYear();
    const mes = String(hoje.getMonth() + 1).padStart(2, '0');
    const dia = String(hoje.getDate()).padStart(2, '0');

    return `${ano}-${mes}-${dia}`;
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

  exibirErroDataAbertura(campoTocado: boolean | null): boolean {
    return (this.formSubmitted || Boolean(campoTocado)) && !this.dataAberturaValida;
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
    this.feedback.confirmar({
      titulo: 'Remover item?',
      mensagem: 'O item será removido desta licitação antes do salvamento.',
      textoConfirmar: 'Remover',
      textoCancelar: 'Cancelar',
      destrutiva: true
    }).then((confirmado) => {
      if (confirmado) {
        this.lista.splice(index, 1);
      }
    });
  }
  ngOnInit(): void {
    const submitbtn = document.querySelector('.btn-submit') as HTMLElement | null;
    const adicionados = document.querySelector('.itens-adicionados') as HTMLElement | null;

    console.log(adicionados)
    submitbtn?.addEventListener("click", ()=>{
      adicionados?.classList.remove('vazia')
    })

    this.licitacao.data_abertura = this.todayDate;
    this.licitacao.atual = false;
    this.carregarLicitacaoAtual();
  }

  onAtualChange(): void {
    this.usuarioAlterouOpcaoAtual = true;
  }

  private carregarLicitacaoAtual(): void {
    this.carregandoLicitacaoAtual = true;
    this.erroAoCarregarLicitacaoAtual = false;

    this.licitacaoService.getAtual().subscribe({
      next: (licitacaoAtual: Licitacao | null) => {
        this.licitacaoAtual = licitacaoAtual;

        if (!this.usuarioAlterouOpcaoAtual) {
          this.licitacao.atual = licitacaoAtual === null;
        }

        this.carregandoLicitacaoAtual = false;
      },
      error: () => {
        this.licitacaoAtual = null;
        this.erroAoCarregarLicitacaoAtual = true;

        if (!this.usuarioAlterouOpcaoAtual) {
          this.licitacao.atual = false;
        }

        this.carregandoLicitacaoAtual = false;
      }
    });
  }

  normalizarCampos(): void {
    this.licitacao.numero_licitacao = this.licitacao.numero_licitacao?.trim().toUpperCase();
    this.licitacao.validade = String(Number(this.licitacao.validade));
    this.licitacao.descricao = this.licitacao.descricao?.trim();
  }

  revisar(event?: Event): void {
    event?.preventDefault();
    this.formSubmitted = true;
    this.errorMessage = '';

    if (!this.podeCriarLicitacao) {
      return;
    }

    this.normalizarCampos();
    this.emRevisao = true;
    setTimeout(() => this.tituloRevisao?.nativeElement.focus());
  }

  voltarParaEdicao(): void {
    if (this.isSaving) {
      return;
    }

    this.errorMessage = '';
    this.emRevisao = false;
  }

  save(){
    this.errorMessage = '';

    if (!this.emRevisao || !this.podeCriarLicitacao) {
      return;
    }

    this.isSaving = true;

    this.licitacaoService.save(this.licitacao).subscribe({
      next: (licitacao: Licitacao) => {
        const id = licitacao.id;
        this.feedback.sucesso('Licitação salva com sucesso.');
        this.router.navigate(['/visualizar-licitacao'], {queryParams: { id }});
      },
      error: () => {
        this.errorMessage = 'Não foi possível salvar a licitação. Revise os campos e tente novamente.';
        this.isSaving = false;
      }
    });
  }
}
