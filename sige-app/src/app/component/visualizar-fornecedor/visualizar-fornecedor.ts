import { Component, ElementRef, ViewChild } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FornecedorService } from '../../service/fornecedor.service';
import { Fornecedor } from '../../model/fornecedor';
import { FormsModule } from '@angular/forms';
import { Endereco } from '../../model/endereco';
import { Modal } from 'bootstrap'
import { EnderecoService } from '../../service/endereco.service';

import { BotaoVoltar } from '../utils/botao-voltar/botao-voltar';
import { FornecedorInsert } from '../../model/fornecedor_insert';
import { FeedbackService } from '../../service/feedback.service';
import { EstadoConteudo } from '../utils/estado-conteudo/estado-conteudo';
import { Acao, pode, Recurso } from '../../security/rbac';
import { UNIDADES_FEDERATIVAS } from '../../model/estados';

@Component({
  selector: 'app-visualizar-fornecedor',
  imports: [BotaoVoltar, FormsModule, EstadoConteudo],
  templateUrl: './visualizar-fornecedor.html',
  styleUrl: './visualizar-fornecedor.scss',
})
export class VisualizarFornecedor {
  readonly pode = pode;
  readonly Acao = Acao;
  readonly Recurso = Recurso;
  readonly unidadesFederativas = UNIDADES_FEDERATIVAS;

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild("myInput") input!: ElementRef;
  @ViewChild('fecharModalInternoBtn') fecharModalInternoBtn!: ElementRef<HTMLButtonElement>;

  constructor(
    private fornecedorService: FornecedorService,
    private enderecoService: EnderecoService,
    private route: ActivatedRoute,
    private router: Router,
    private feedback: FeedbackService
  ) { }


  fornecedor = <Fornecedor>{};
  fornecedor_editar = <FornecedorInsert>{};
  endereco_editar = <Endereco>{};
  formSubmitted: boolean = false;
  isSaving: boolean = false;
  errorMessageModal: string = '';
  isLoadingPage: boolean = true;
  errorMessagePage: string = '';
  idPagina: number | null = null;
  private permitirFecharModalSemConfirmacao: boolean = false;

  private limparNumero(valor: string | undefined): string {
    return (valor || '').replace(/\D/g, '');
  }

  private limitarTexto(valor: string | undefined, maximo: number): string {
    return (valor || '').slice(0, maximo);
  }

  onRazaoSocialInput(): void {
    this.fornecedor_editar.razao_social = this.limitarTexto(this.fornecedor_editar.razao_social, 255);
  }

  onNomeFantasiaInput(): void {
    this.fornecedor_editar.nome_fantasia = this.limitarTexto(this.fornecedor_editar.nome_fantasia, 255);
  }

  onCnpjInput(): void {
    const digitos = this.limparNumero(this.fornecedor_editar.cnpj).slice(0, 14);

    if (digitos.length <= 2) {
      this.fornecedor_editar.cnpj = digitos;
      return;
    }

    if (digitos.length <= 5) {
      this.fornecedor_editar.cnpj = `${digitos.slice(0, 2)}.${digitos.slice(2)}`;
      return;
    }

    if (digitos.length <= 8) {
      this.fornecedor_editar.cnpj = `${digitos.slice(0, 2)}.${digitos.slice(2, 5)}.${digitos.slice(5)}`;
      return;
    }

    if (digitos.length <= 12) {
      this.fornecedor_editar.cnpj = `${digitos.slice(0, 2)}.${digitos.slice(2, 5)}.${digitos.slice(5, 8)}/${digitos.slice(8)}`;
      return;
    }

    this.fornecedor_editar.cnpj = `${digitos.slice(0, 2)}.${digitos.slice(2, 5)}.${digitos.slice(5, 8)}/${digitos.slice(8, 12)}-${digitos.slice(12, 14)}`;
  }

  onLogradouroInput(): void {
    this.endereco_editar.lagradouro = this.limitarTexto(this.endereco_editar.lagradouro, 255);
  }

  onCepInput(): void {
    const digitos = this.limparNumero(this.endereco_editar.cep).slice(0, 8);
    if (digitos.length <= 5) {
      this.endereco_editar.cep = digitos;
      return;
    }

    this.endereco_editar.cep = `${digitos.slice(0, 5)}-${digitos.slice(5)}`;
  }

  onNumeroEnderecoInput(): void {
    this.endereco_editar.numero = this.limitarTexto(this.endereco_editar.numero, 20);
  }

  onBairroInput(): void {
    this.endereco_editar.bairro = this.limitarTexto(this.endereco_editar.bairro, 100);
  }

  onMunicipioInput(): void {
    this.endereco_editar.municipio = this.limitarTexto(this.endereco_editar.municipio, 100);
  }

  onTelefoneInput(): void {
    const digitos = this.limparNumero(this.fornecedor_editar.telefone).slice(0, 11);

    if (digitos.length === 0) {
      this.fornecedor_editar.telefone = '';
      return;
    }

    if (digitos.length <= 2) {
      this.fornecedor_editar.telefone = `(${digitos}`;
      return;
    }

    const ddd = digitos.slice(0, 2);
    const restante = digitos.slice(2);

    if (digitos.length <= 10) {
      if (restante.length <= 4) {
        this.fornecedor_editar.telefone = `(${ddd}) ${restante}`;
        return;
      }
      this.fornecedor_editar.telefone = `(${ddd}) ${restante.slice(0, 4)}-${restante.slice(4)}`;
      return;
    }

    if (restante.length <= 5) {
      this.fornecedor_editar.telefone = `(${ddd}) ${restante}`;
      return;
    }

    this.fornecedor_editar.telefone = `(${ddd}) ${restante.slice(0, 5)}-${restante.slice(5)}`;
  }

  onEmailInput(): void {
    this.fornecedor_editar.email = this.limitarTexto(this.fornecedor_editar.email, 255);
  }

  get cnpjValido(): boolean {
    return this.limparNumero(this.fornecedor_editar.cnpj).length === 14;
  }

  get emailValido(): boolean {
    const email = (this.fornecedor_editar.email || '').trim();
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  get telefoneValido(): boolean {
    const telefone = this.limparNumero(this.fornecedor_editar.telefone);
    return telefone.length >= 10 && telefone.length <= 11;
  }

  get cepValido(): boolean {
    return this.limparNumero(this.endereco_editar.cep).length === 8;
  }

  get estadoValido(): boolean {
    return this.unidadesFederativas.some(uf => uf.sigla === this.endereco_editar.estado);
  }

  get fornecedorFormValido(): boolean {
    return Boolean(
      this.fornecedor_editar.razao_social?.trim() &&
      this.fornecedor_editar.nome_fantasia?.trim() &&
      this.cnpjValido &&
      this.endereco_editar.lagradouro?.trim() &&
      this.cepValido &&
      this.endereco_editar.numero?.trim() &&
      this.endereco_editar.bairro?.trim() &&
      this.endereco_editar.municipio?.trim() &&
      this.estadoValido &&
      this.telefoneValido &&
      this.emailValido
    );
  }

  get possuiDadosModalPreenchidos(): boolean {
    return Boolean(
      this.fornecedor_editar.razao_social ||
      this.fornecedor_editar.nome_fantasia ||
      this.fornecedor_editar.cnpj ||
      this.endereco_editar.lagradouro ||
      this.endereco_editar.cep ||
      this.endereco_editar.numero ||
      this.endereco_editar.bairro ||
      this.endereco_editar.municipio ||
      this.endereco_editar.estado ||
      this.fornecedor_editar.telefone ||
      this.fornecedor_editar.email
    );
  }


  ngOnInit() {
    const id = Number(this.route.snapshot.queryParamMap.get('id'));

    if (!Number.isInteger(id) || id <= 0) {
      this.isLoadingPage = false;
      this.errorMessagePage = 'Não foi possível identificar o registro solicitado.';
      return;
    }

    this.idPagina = id;
    this.get(id, true);
  }

  ngAfterViewInit() {

    const modalElement = this.modal.nativeElement;

    modalElement.addEventListener('shown.bs.modal', () => {
      this.input?.nativeElement?.focus();
    });

    modalElement.addEventListener('hide.bs.modal', (event: Event) => {
      if (this.permitirFecharModalSemConfirmacao) {
        this.permitirFecharModalSemConfirmacao = false;
        return;
      }

      if (this.isSaving) {
        event.preventDefault();
        return;
      }

      if (this.possuiDadosModalPreenchidos) {
        event.preventDefault();
        this.confirmarDescarteModal();
      }
    });

  }

  carregar_Fornecedor() {
    this.formSubmitted = false;
    this.errorMessageModal = '';
    this.fornecedor_editar.id = this.fornecedor.id;
    this.fornecedor_editar.cnpj = this.fornecedor.cnpj;
    this.fornecedor_editar.razao_social = this.fornecedor.razao_social;
    this.fornecedor_editar.nome_fantasia = this.fornecedor.nome_fantasia;
    this.fornecedor_editar.telefone = this.fornecedor.telefone;
    this.fornecedor_editar.email = this.fornecedor.email;
    this.fornecedor_editar.endereco = this.fornecedor.endereco.id;
    this.endereco_editar.id = this.fornecedor.endereco.id;
    this.endereco_editar.lagradouro = this.fornecedor.endereco.lagradouro;
    this.endereco_editar.numero = this.fornecedor.endereco.numero;
    this.endereco_editar.bairro = this.fornecedor.endereco.bairro;
    this.endereco_editar.municipio = this.fornecedor.endereco.municipio;
    this.endereco_editar.estado = this.fornecedor.endereco.estado;
    this.endereco_editar.cep = this.fornecedor.endereco.cep;
  }

  get(id: number, controlarEstadoPagina: boolean = false): void {
    if (controlarEstadoPagina) {
      this.isLoadingPage = true;
      this.errorMessagePage = '';
    }

    this.fornecedorService.getById(id).subscribe(
      {
        next: (reposta: Fornecedor) => {
          this.fornecedor = reposta;
          if (controlarEstadoPagina) {
            this.isLoadingPage = false;
          }
        },
        error: () => {
          if (controlarEstadoPagina) {
            this.isLoadingPage = false;
            this.errorMessagePage = 'Não foi possível carregar este fornecedor no momento.';
          }
        }
      }
    )
  }

  recarregarPagina(): void {
    if (this.idPagina !== null) {
      this.get(this.idPagina, true);
    }
  }

  saveFornecedo(): void {
    this.fornecedorService.save(this.fornecedor_editar).subscribe(
      {
        complete: () => {
          this.isSaving = false;
          this.fecharModalSemConfirmacao();
          this.feedback.sucesso('Fornecedor atualizado com sucesso.');
          this.get(this.fornecedor.id);
        },
        error: () => {
          this.isSaving = false;
          this.errorMessageModal = 'Endereço salvo, mas houve erro ao atualizar o fornecedor. Tente novamente.';
        }
      }
    )
  }

  save(): void {
    this.formSubmitted = true;
    this.errorMessageModal = '';

    if (this.isSaving || !this.fornecedorFormValido) {
      return;
    }

    this.isSaving = true;

    this.enderecoService.save(this.endereco_editar).subscribe(
      {
        complete: () => {
          this.saveFornecedo();
        },
        error: () => {
          this.isSaving = false;
          this.errorMessageModal = 'Não foi possível salvar o endereço. Verifique os dados e tente novamente.';
        }
      }
    )
  }

  excluirFornecedor(): void {
    if (!this.fornecedor.id || this.isSaving) {
      return;
    }

    this.feedback.confirmar({
      titulo: 'Excluir fornecedor?',
      mensagem: `Esta ação removerá permanentemente o fornecedor "${this.fornecedor.razao_social}".`,
      textoConfirmar: 'Excluir',
      textoCancelar: 'Cancelar',
      destrutiva: true
    }).then((confirmou) => {
      if (!confirmou) {
        return;
      }

      this.isSaving = true;
      this.fornecedorService.delete(this.fornecedor.id).subscribe({
        next: () => {
          this.isSaving = false;
          this.feedback.sucesso('Fornecedor excluído com sucesso.');
          this.router.navigate(['/visualizar-fornecedores']);
        },
        error: (erro) => {
          this.isSaving = false;
          this.feedback.erro(
            erro?.error?.detail || 'Não foi possível excluir o fornecedor. Tente novamente.',
            'Erro ao excluir fornecedor'
          );
        }
      });
    });
  }

  tentarFecharModal(): void {
    if (this.isSaving) {
      return;
    }

    if (this.possuiDadosModalPreenchidos) {
      this.confirmarDescarteModal();
      return;
    }

    this.fecharModalSemConfirmacao();
  }

  private confirmarDescarteModal(): void {
    this.feedback.confirmar({
      titulo: 'Descartar alterações?',
      mensagem: 'Você já preencheu dados do fornecedor. Se sair agora, perderá toda a operação. Deseja sair mesmo assim?',
      textoConfirmar: 'Descartar',
      textoCancelar: 'Continuar editando',
      destrutiva: true
    }).then((desejaSair) => {
      if (desejaSair) {
        this.fecharModalSemConfirmacao();
      }
    });
  }

  private fecharModalSemConfirmacao(): void {
    if (this.fecharModalInternoBtn?.nativeElement) {
      this.permitirFecharModalSemConfirmacao = true;
      this.fecharModalInternoBtn.nativeElement.click();
    }
  }
}
