import { FiltroConfig } from './../../model/filtro-config';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Paginacao } from '../utils/paginacao/paginacao';
import { Router } from '@angular/router';
import { ItemGenericoService } from '../../service/item-generico.service';
import { ItemGenerico } from '../../model/item_generico';
import { FormsModule } from '@angular/forms';
import { FeedbackService } from '../../service/feedback.service';
import { EstadoConteudo } from '../utils/estado-conteudo/estado-conteudo';
import { Acao, pode, Recurso } from '../../security/rbac';
import { EstadoListagemService } from '../../service/estado-listagem.service';

@Component({
  selector: 'app-visualizar-gens-alimenticios',
  standalone: true,
  imports: [BarraPesquisa, FormsModule, Paginacao, EstadoConteudo],
  templateUrl: './visualizar-gens-alimenticios.html',
  styleUrl: './visualizar-gens-alimenticios.scss',
})
export class VisualizarGensAlimenticios {
  readonly pode = pode;
  readonly Acao = Acao;
  readonly Recurso = Recurso;

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild('myInput') input!: ElementRef;
  @ViewChild('fecharModalInternoBtn') fecharModalInternoBtn!: ElementRef<HTMLButtonElement>;

  filtros: FiltroConfig[] = [
  {
    campo: 'categoria',
    label: 'Categoria',
    tipo: 'checkbox',
    opcoes: []
  },
  {
    campo: 'unidade_medida',
    label: 'Unidade de medida',
    tipo: 'checkbox',
    opcoes: []
  }
];

filtrosAtivos: any = {};

  constructor(
    private ItemGenericoService: ItemGenericoService,
    private router: Router,
    private feedback: FeedbackService,
    private estadoListagem: EstadoListagemService
  ) { }

  registros: ItemGenerico[] = [];
  currentPage: number = 1;
  pageSize: number = 5;
  total: number = 0;
  hasNext: boolean = false;
  hasPrev: boolean = false;
  termoBuscaAtual: string = '';
  isLoadingPage: boolean = false;
  errorMessagePage: string = '';
  registroEditar: ItemGenerico = <ItemGenerico>{};
  registroOriginalModal: ItemGenerico | null = null;
  formSubmitted: boolean = false;
  isSaving: boolean = false;
  errorMessageModal: string = '';
  private permitirFecharModalSemConfirmacao: boolean = false;

  unidade_medida = {
    "KG": "Quilograma(KG)",
    "G": "Grama(G)",
    "L": "Litro(L)",
    "mL": "Mililitro(mL)",
    "duzia": "Duzia",
    "cento": "Cento",
    "PCT": "Pacote(PCT)",
    "CX": "Caixa(CX)",
    "FND": "Fardo(FND)",
    "GAR": "Garrafa(GAR)",
    "lata": "Lata",
    "un": "Unidade(UN)"
  };

  categoria = {
    "tempS": "Tempero Secos",
    "SM": "Secos / Mercearia",
    "Lac": "Lácteos e Derivados",
    "Oli": "Óleos, Azeites e Vinagres",
    "MolCo": "Molhos e Condimentos",
    "Fr": "Frutas",
    "Le": "Legumes",
    "Pr": "Proteínas"
  };

  categoriasDisponiveis = Object.keys(this.categoria);
  unidadesDisponiveis = Object.keys(this.unidade_medida);

  getItens(termobusca?: string) {
    if (termobusca !== undefined) {
      this.termoBuscaAtual = termobusca;
      this.currentPage = 1;
      this.salvarEstadoListagem();
    }

    this.isLoadingPage = true;
    this.errorMessagePage = '';

    this.ItemGenericoService.get(this.termoBuscaAtual, this.currentPage, this.pageSize, this.normalizarFiltrosParaEnvio()).subscribe({
      next: (resposta) => {
        this.registros = resposta.results;
        this.total = resposta.count;
        this.hasNext = Boolean(resposta.next);
        this.hasPrev = Boolean(resposta.previous);
        this.isLoadingPage = false;
      },
      error: () => {
        this.isLoadingPage = false;
        this.errorMessagePage = 'Não foi possível carregar os gêneros alimentícios no momento.';
      }
    });

  }

  private normalizarFiltrosParaEnvio(): any {
    const filtros = { ...this.filtrosAtivos };

    Object.entries(filtros).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        delete filtros[key];

        if (value.length === 1) {
          filtros[key] = value[0];
        } else if (value.length > 1) {
          filtros[`${key}__in`] = value.join(',');
        }
      }
    });

    return filtros;
  }

  ngOnInit() {
    this.filtros[0].opcoes = this.categoriasDisponiveis.map(cat => ({
      id: cat,
      nome: this.getCategoriaLabel(cat)
    }));

    this.filtros[1].opcoes = this.unidadesDisponiveis.map(un => ({
      id: un,
      nome: this.getUnidadeMedidaLabel(un)
    }));

    this.restaurarEstadoListagem();
    this.getItens();
  }

  proximaPagina(): void {
    if (!this.hasNext) {
      return;
    }

    this.currentPage += 1;
    this.salvarEstadoListagem();
    this.getItens();
  }

  paginaAnterior(): void {
    if (!this.hasPrev || this.currentPage === 1) {
      return;
    }

    this.currentPage -= 1;
    this.salvarEstadoListagem();
    this.getItens();
  }

  irParaPagina(page: number): void {
    if (page === this.currentPage) {
      return;
    }

    this.currentPage = page;
    this.salvarEstadoListagem();
    this.getItens();
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

      if (this.possuiDadosAlteradosModal) {
        event.preventDefault();
        this.confirmarDescarteModal();
      }
    });
  }

  enviarPara(rota: string, id?: number) {
    this.salvarEstadoListagem();

    if (id) {
      this.router.navigate([rota], { queryParams: { id } });
    }
    else {
      this.router.navigate([rota]);
    }
  }

  get modoCadastro(): boolean {
    return !this.registroEditar.id;
  }

  novoRegistro(): void {
    this.carregarRegistro(<ItemGenerico>{ catmat: '', descricao: '', unidade_medida: '', categoria: '' });
  }

  carregarRegistro(registro: ItemGenerico) {
    this.formSubmitted = false;
    this.errorMessageModal = '';
    this.registroOriginalModal = { ...registro };
    this.registroEditar = { ...registro };
  }

  onCatmatInput(): void {
    this.registroEditar.catmat = (this.registroEditar.catmat || '')
      .replace(/\D/g, '')
      .slice(0, 6);
  }

  onDescricaoInput(): void {
    this.registroEditar.descricao = (this.registroEditar.descricao || '').slice(0, 300);
  }

  get catmatValido(): boolean {
    const catmat = (this.registroEditar.catmat || '').trim();
    return /^\d{6}$/.test(catmat);
  }

  get descricaoValida(): boolean {
    const descricao = (this.registroEditar.descricao || '').trim();
    return descricao.length > 0 && descricao.length <= 300;
  }

  get categoriaValida(): boolean {
    return Boolean(this.registroEditar.categoria?.trim());
  }

  get unidadeValida(): boolean {
    return Boolean(this.registroEditar.unidade_medida?.trim());
  }

  get formularioValido(): boolean {
    return this.catmatValido && this.descricaoValida && this.categoriaValida && this.unidadeValida;
  }

  get possuiDadosAlteradosModal(): boolean {
    if (!this.registroOriginalModal) {
      return false;
    }

    return (
      (this.registroOriginalModal.catmat || '') !== (this.registroEditar.catmat || '') ||
      (this.registroOriginalModal.categoria || '') !== (this.registroEditar.categoria || '') ||
      (this.registroOriginalModal.unidade_medida || '') !== (this.registroEditar.unidade_medida || '') ||
      (this.registroOriginalModal.descricao || '') !== (this.registroEditar.descricao || '')
    );
  }

  getUnidadeMedida(item: ItemGenerico): string {
    const unidade = this.unidade_medida[item.unidade_medida as keyof typeof this.unidade_medida];
    return unidade ? unidade : item.unidade_medida;
  }

  getCategoria(item: ItemGenerico): string {
    const categoria = this.categoria[item.categoria as keyof typeof this.categoria];
    return categoria ? categoria : item.categoria;
  }

  getCategoriaLabel(chave: string): string {
    const categoria = this.categoria[chave as keyof typeof this.categoria];
    return categoria ? categoria : chave;
  }

  getUnidadeMedidaLabel(chave: string): string {
    const unidade = this.unidade_medida[chave as keyof typeof this.unidade_medida];
    return unidade ? unidade : chave;
  }

  salvarRegistro() {
    this.formSubmitted = true;
    this.errorMessageModal = '';

    if (this.isSaving || !this.formularioValido) {
      return;
    }

    this.isSaving = true;

    this.ItemGenericoService.save(this.registroEditar).subscribe({
      next: () => {
        this.isSaving = false;
        this.fecharModalSemConfirmacao();
        this.feedback.sucesso('Gênero alimentício atualizado com sucesso.');
        this.getItens();
      },
      error: (erro) => {
        this.isSaving = false;
        if (erro?.error?.catmat) {
          this.errorMessageModal = 'Já existe um gênero alimentício cadastrado com este CATMAT.';
          return;
        }
        this.errorMessageModal = this.modoCadastro
          ? 'Não foi possível cadastrar o gênero alimentício. Verifique os dados e tente novamente.'
          : 'Não foi possível salvar as alterações. Verifique os dados e tente novamente.';
      }
    });
  }

  tentarFecharModal(): void {
    if (this.isSaving) {
      return;
    }

    if (this.possuiDadosAlteradosModal) {
      this.confirmarDescarteModal();
      return;
    }

    this.fecharModalSemConfirmacao();
  }

  private confirmarDescarteModal(): void {
    this.feedback.confirmar({
      titulo: 'Descartar alterações?',
      mensagem: 'Você alterou dados do gênero alimentício. Se sair agora, perderá toda a operação. Deseja sair mesmo assim?',
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

  aplicarFiltros(filtros: any) {
    this.filtrosAtivos = { ...filtros };
    this.currentPage = 1;
    this.salvarEstadoListagem();
    this.getItens();
  }

  private restaurarEstadoListagem(): void {
    const estado = this.estadoListagem.obter('generos');
    if (!estado) {
      return;
    }

    this.termoBuscaAtual = estado.termoBuscaAtual;
    this.filtrosAtivos = { ...estado.filtrosAtivos };
    this.currentPage = estado.currentPage;
  }

  salvarEstadoListagem(): void {
    this.estadoListagem.salvar('generos', {
      termoBuscaAtual: this.termoBuscaAtual,
      filtrosAtivos: this.filtrosAtivos,
      currentPage: this.currentPage
    });
  }

}
