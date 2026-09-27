import { Component, ElementRef, ViewChild } from '@angular/core';
import { Router } from '@angular/router';
import { UsuarioService } from '../../service/usuario.service';
import { Usuario } from '../../model/usuario';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Paginacao } from '../utils/paginacao/paginacao';
<<<<<<< HEAD
import { FeedbackService } from '../../service/feedback.service';
import { EstadoConteudo } from '../utils/estado-conteudo/estado-conteudo';
=======
import { Papel } from '../../security/rbac';
>>>>>>> origin/marcos

@Component({
  selector: 'app-visualizar-usuarios',
  standalone: true,
  imports: [CommonModule, FormsModule, BarraPesquisa, Paginacao, EstadoConteudo],
  templateUrl: './visualizar-usuarios.html',
  styleUrl: './visualizar-usuarios.scss',
})
export class VisualizarUsuarios {

  constructor(
    private router: Router,
    private usuarioService: UsuarioService,
    private feedback: FeedbackService
  ) { }

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild('myInput') input?: ElementRef;
  @ViewChild('fecharModalInternoBtn') fecharModalInternoBtn!: ElementRef<HTMLButtonElement>;

  usuarios: Usuario[] = [];
  registro: Usuario = <Usuario>{ papel: '' };
  mostrarSenha = false;
  mensagemBotao = "Adicionar Novo Usuario";
  formSubmitted: boolean = false;
  isSaving: boolean = false;
  isLoadingUsuarios: boolean = false;
  errorMessagePage: string = '';
  errorMessageModal: string = '';
  currentPage: number = 1;
  pageSize: number = 5;
  total: number = 0;
  hasNext: boolean = false;
  hasPrev: boolean = false;
  termoBuscaAtual: string = '';
  private permitirFecharModalSemConfirmacao: boolean = false;
  private usuarioAtualId: number | null = null;
  private estadoInicialModal: { username: string; email: string; first_name: string; last_name: string; papel: string; password: string } = {
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    papel: '',
    password: ''
  };

  get isEditando(): boolean {
    return Boolean(this.registro.id);
  }

  get tituloModal(): string {
    return this.isEditando ? 'ATUALIZAR USUÁRIO' : 'ADICIONAR USUÁRIO';
  }

  get usernameValido(): boolean {
    const username = (this.registro.username || '').trim();
    return /^[a-zA-Z0-9._-]{3,150}$/.test(username);
  }

  get emailValido(): boolean {
    const email = (this.registro.email || '').trim();
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  get nomeValido(): boolean {
    const nome = (this.registro.first_name || '').trim();
    return nome.length >= 2 && nome.length <= 150;
  }

  get sobrenomeValido(): boolean {
    const sobrenome = (this.registro.last_name || '').trim();
    return sobrenome.length >= 2 && sobrenome.length <= 150;
  }

  get papelValido(): boolean {
    const papel = (this.registro.papel || '').trim();
    return papel === Papel.DIRETOR || papel === Papel.TECNICO_ADMINISTRATIVO || papel === Papel.NUTRICIONISTA || papel === Papel.ESTOQUISTA;
  }

  get senhaObrigatoria(): boolean {
    return !this.isEditando;
  }

  get senhaValida(): boolean {
    const senha = (this.registro.password || '').trim();

    if (this.senhaObrigatoria) {
      return senha.length >= 6 && senha.length <= 128;
    }

    if (senha.length === 0) {
      return true;
    }

    return senha.length >= 6 && senha.length <= 128;
  }

  get formularioValido(): boolean {
    return this.usernameValido && this.emailValido && this.nomeValido && this.sobrenomeValido && this.papelValido && this.senhaValida;
  }

  get podeSalvarUsuario(): boolean {
    return !this.isSaving && this.formularioValido;
  }

  get possuiDadosModalPreenchidos(): boolean {
    const estadoAtual = this.snapshotRegistro(this.registro);

    return JSON.stringify(estadoAtual) !== JSON.stringify(this.estadoInicialModal);
  }

  ngOnInit() {
    this.usuarioAtualId = this.obterUsuarioAtualId();
    this.getUsuarios();
  }

  private obterUsuarioAtualId(): number | null {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return null;
    }

    try {
      const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      const payload = JSON.parse(atob(base64));
      const userId = Number(payload?.user_id);
      return Number.isFinite(userId) ? userId : null;
    } catch {
      return null;
    }
  }

  isUsuarioAtual(usuario: Usuario): boolean {
    return usuario.id === this.usuarioAtualId;
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

  getUsuarios(termobusca?: string) {
    if (termobusca !== undefined) {
      this.termoBuscaAtual = termobusca;
      this.currentPage = 1;
    }

    this.isLoadingUsuarios = true;
    this.errorMessagePage = '';

    this.usuarioService.get(this.termoBuscaAtual, this.currentPage, this.pageSize).subscribe(
      {
        next: (registro) => {
          this.usuarios = registro.results;
          this.total = registro.count;
          this.hasNext = Boolean(registro.next);
          this.hasPrev = Boolean(registro.previous);
          this.isLoadingUsuarios = false;
        },
        error: () => {
          this.isLoadingUsuarios = false;
          this.errorMessagePage = 'Não foi possível carregar os usuários no momento.';
        }
      }
    );
  }

  proximaPagina(): void {
    if (!this.hasNext) {
      return;
    }

    this.currentPage += 1;
    this.getUsuarios();
  }

  paginaAnterior(): void {
    if (!this.hasPrev || this.currentPage === 1) {
      return;
    }

    this.currentPage -= 1;
    this.getUsuarios();
  }

  irParaPagina(page: number): void {
    if (page === this.currentPage) {
      return;
    }

    this.currentPage = page;
    this.getUsuarios();
  }

  verificarPapel(papel: string): string {
    if (papel === Papel.DIRETOR) {
      return 'Diretor';
    }
    if (papel === Papel.NUTRICIONISTA) {
      return 'Nutricionista';
    }
    if (papel === Papel.ESTOQUISTA) {
      return 'Estoquista';
    }
    return 'Técnico Administrativo';
  }

  verificarStatus(status: boolean): string {
    if (status) {
      return 'Ativo';
    }
    return 'Inativo';
  }

  classStatus(status: boolean): string {
    if (!status) {
      return "bg-danger text-white";
    }
    else {
      return "bg-success text-white";
    }
  }

  toggleSenha() {
    if (this.isSaving) {
      return;
    }

    this.mostrarSenha = !this.mostrarSenha;
  }

  private limitarTexto(valor: string | undefined, maximo: number): string {
    return (valor || '').slice(0, maximo);
  }

  onUsernameInput(): void {
    this.registro.username = this.limitarTexto(this.registro.username, 150)
      .replace(/\s+/g, '')
      .replace(/[^a-zA-Z0-9._-]/g, '');
  }

  onEmailInput(): void {
    this.registro.email = this.limitarTexto(this.registro.email, 255);
  }

  onNomeInput(): void {
    this.registro.first_name = this.limitarTexto(this.registro.first_name, 150);
  }

  onSobrenomeInput(): void {
    this.registro.last_name = this.limitarTexto(this.registro.last_name, 150);
  }

  onSenhaInput(): void {
    this.registro.password = this.limitarTexto(this.registro.password, 128);
  }

  private snapshotRegistro(registro: Usuario): { username: string; email: string; first_name: string; last_name: string; papel: string; password: string } {
    return {
      username: (registro.username || '').trim(),
      email: (registro.email || '').trim(),
      first_name: (registro.first_name || '').trim(),
      last_name: (registro.last_name || '').trim(),
      papel: (registro.papel || '').trim(),
      password: (registro.password || '').trim()
    };
  }

  private atualizarEstadoInicialModal(): void {
    this.estadoInicialModal = this.snapshotRegistro(this.registro);
  }

  private extrairMensagemErro(error: any): string {
    const dados = error?.error;

    if (typeof dados === 'string' && dados.trim()) {
      return dados;
    }

    if (dados && typeof dados === 'object') {
      const mensagens = Object.values(dados)
        .flatMap((valor) => Array.isArray(valor) ? valor : [valor])
        .filter((valor) => typeof valor === 'string' && valor.trim()) as string[];

      if (mensagens.length > 0) {
        return mensagens[0];
      }
    }

    return 'Não foi possível salvar o usuário. Verifique os dados e tente novamente.';
  }

  private construirPayload(): any {
    const payload: any = {
      username: (this.registro.username || '').trim(),
      email: (this.registro.email || '').trim(),
      first_name: (this.registro.first_name || '').trim(),
      last_name: (this.registro.last_name || '').trim(),
      papel: (this.registro.papel || '').trim()
    };

    const senha = (this.registro.password || '').trim();
    if (senha) {
      payload.password = senha;
    }

    return payload;
  }


  reiniciarRegistro(): void {
    if (this.isSaving) {
      return;
    }

    this.registro = <Usuario>{ papel: '' };
    this.mensagemBotao = "Adicionar Novo Usuario";
    this.formSubmitted = false;
    this.errorMessageModal = '';
    this.mostrarSenha = false;
    this.atualizarEstadoInicialModal();
  }

  carregarRegistro(usuario: Usuario): void {
    if (this.isSaving) {
      return;
    }

    this.registro = { ...usuario };
    this.registro.password = '';
    this.mensagemBotao = "Atualizar Usuario";
    this.formSubmitted = false;
    this.errorMessageModal = '';
    this.mostrarSenha = false;
    this.atualizarEstadoInicialModal();

  }

  saveUsuario(): void {
    this.formSubmitted = true;
    this.errorMessageModal = '';

    if (!this.podeSalvarUsuario) {
      return;
    }

    const editando = this.isEditando;

    this.feedback.confirmar({
      titulo: editando ? 'Confirmar alterações' : 'Confirmar cadastro',
      mensagem: editando ? 'Deseja atualizar este usuário?' : 'Deseja salvar este usuário?',
      textoConfirmar: editando ? 'Atualizar' : 'Salvar',
      textoCancelar: 'Cancelar'
    }).then((confirmado) => {
      if (!confirmado || this.isSaving) {
        return;
      }

      this.isSaving = true;
      const payload = this.construirPayload();

      if (!this.registro.id) {
        this.usuarioService.save(payload).subscribe({
          next: () => this.concluirSalvamentoUsuario(false),
          error: (error) => {
            this.errorMessageModal = this.extrairMensagemErro(error);
            this.isSaving = false;
          }
        });
        return;
      }

      this.usuarioService.patch(this.registro.id, payload).subscribe({
        next: () => this.concluirSalvamentoUsuario(true),
        error: (error) => {
          this.errorMessageModal = this.extrairMensagemErro(error);
          this.isSaving = false;
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

  desativarAtivarUsuario(usuario: Usuario): void {
    const novoStatus = !usuario.is_active;
    const desativando = Boolean(usuario.is_active);

    this.feedback.confirmar({
      titulo: desativando ? 'Desativar usuário?' : 'Ativar usuário?',
      mensagem: desativando ? 'Deseja desativar este usuário?' : 'Deseja ativar este usuário?',
      textoConfirmar: desativando ? 'Desativar' : 'Ativar',
      textoCancelar: 'Cancelar',
      destrutiva: desativando
    }).then((confirmado) => {
      if (!confirmado) {
        return;
      }

      this.usuarioService.patch(usuario.id, { is_active: novoStatus }).subscribe({
        next: () => {
          usuario.is_active = novoStatus;
          this.feedback.sucesso(novoStatus ? 'Usuário ativado com sucesso.' : 'Usuário desativado com sucesso.');
        },
        error: () => {
          this.feedback.erro('Não foi possível atualizar o status do usuário.');
        }
      });
    });
  }

  private concluirSalvamentoUsuario(editando: boolean): void {
    this.isSaving = false;
    this.fecharModalSemConfirmacao();
    this.feedback.sucesso(editando ? 'Usuário atualizado com sucesso.' : 'Usuário cadastrado com sucesso.');
    this.getUsuarios();
  }

  private confirmarDescarteModal(): void {
    this.feedback.confirmar({
      titulo: 'Descartar alterações?',
      mensagem: 'Você já preencheu dados do usuário. Se sair agora, perderá toda a operação. Deseja sair mesmo assim?',
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
<<<<<<< HEAD
=======

  desativarAtivarUsuario(usuario: Usuario): void {
    if (usuario.is_active && this.isUsuarioAtual(usuario)) {
      alert('Você não pode desativar a própria conta.');
      return;
    }

    let mensagem = "";
    if (usuario.is_active) {
      mensagem = 'Tem certeza que deseja desativar este usuário?';
    }
    else {
      mensagem = 'Tem certeza que deseja ativar este usuário?';
    }
    const confirmar = confirm(mensagem);
    if (!confirmar) {
      return;
    }
    const novoStatus = !usuario.is_active;
    this.usuarioService.patch(usuario.id, { is_active: novoStatus }).subscribe(
      {
        next: (registro: Usuario) => {
          usuario.is_active = registro.is_active;
        },
        error: (error) => {
          alert(this.extrairMensagemErro(error));
        }
      }
    );
  }
>>>>>>> origin/marcos
}
