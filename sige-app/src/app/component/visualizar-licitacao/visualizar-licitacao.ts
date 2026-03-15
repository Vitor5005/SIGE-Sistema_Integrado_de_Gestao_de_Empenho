import { Component, ElementRef, ViewChild } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LicitacaoService } from '../../service/licitacao.service';
import { Licitacao } from '../../model/licitacao';
import { CommonModule } from '@angular/common';
import { AtaService } from '../../service/ata.service';
import { Ata } from '../../model/ata';
import { BotaoVoltar } from "../utils/botao-voltar/botao-voltar";
import { Fornecedor } from '../../model/fornecedor';
import { Endereco } from '../../model/endereco';
import { FormsModule } from '@angular/forms';
import { VisualizarFornecedores } from '../visualizar-fornecedores/visualizar-fornecedores';
import { FornecedorService } from '../../service/fornecedor.service';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Paginacao } from '../utils/paginacao/paginacao';
import { AtaInsert } from '../../model/ata_insert';
import { FornecedorInsert } from '../../model/fornecedor_insert';
import { EnderecoService } from '../../service/endereco.service';
import { EmpenhoInsert } from '../../model/empenho_insert';
import { EmpenhoService } from '../../service/empenho.service';

@Component({
  selector: 'app-visualizar-licitacao',
  imports: [CommonModule, BotaoVoltar, FormsModule, BarraPesquisa, Paginacao],
  templateUrl: './visualizar-licitacao.html',
  styleUrl: './visualizar-licitacao.scss',
})
export class VisualizarLicitacao {

  constructor(
    private router: Router,
    private licitacaoService: LicitacaoService,
    private fornecedorService: FornecedorService,
    private enderecoService: EnderecoService,
    private empenhoService: EmpenhoService,
    private ataService: AtaService,
    private route: ActivatedRoute
  ) { }

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild("myInput") input!: ElementRef;
  @ViewChild('fecharModalInternoBtn') fecharModalInternoBtn!: ElementRef<HTMLButtonElement>;

  licitacao: Licitacao = <Licitacao>{};
  atas: Array<Ata> = Array<Ata>();
  fornecedores: Fornecedor[] = [];
  fornecedores_licitados: number[] = [];
  currentPageAtas: number = 1;
  pageSizeAtas: number = 5;
  totalAtas: number = 0;
  hasNextAtas: boolean = false;
  hasPrevAtas: boolean = false;
  currentPageFornecedores: number = 1;
  pageSizeFornecedores: number = 5;
  totalFornecedores: number = 0;
  hasNextFornecedores: boolean = false;
  hasPrevFornecedores: boolean = false;
  termoBuscaFornecedor: string = '';

  fornecedor_insercao: FornecedorInsert = <FornecedorInsert>{};
  endereco_insercao: Endereco = <Endereco>{};
  ata_insercao: AtaInsert = <AtaInsert>{ ata_saldo_total: 0 };
  empenho_insercao: EmpenhoInsert = <EmpenhoInsert>{ saldo_utilizado: 0, quantidade_itens: 0, valor_total: 0 };

  modal_page: number = 0;
  jump_page: boolean = false;
  formSubmittedPage1: boolean = false;
  formSubmittedPage2: boolean = false;
  isSaving: boolean = false;
  errorMessageModal: string = '';
  private permitirFecharModalSemConfirmacao: boolean = false;

  private limparNumero(valor: string | undefined): string {
    return (valor || '').replace(/\D/g, '');
  }

  private limitarTexto(valor: string | undefined, maximo: number): string {
    return (valor || '').slice(0, maximo);
  }

  onRazaoSocialInput(): void {
    this.fornecedor_insercao.razao_social = this.limitarTexto(this.fornecedor_insercao.razao_social, 255);
  }

  onNomeFantasiaInput(): void {
    this.fornecedor_insercao.nome_fantasia = this.limitarTexto(this.fornecedor_insercao.nome_fantasia, 255);
  }

  onCnpjInput(): void {
    const digitos = this.limparNumero(this.fornecedor_insercao.cnpj).slice(0, 14);

    if (digitos.length <= 2) {
      this.fornecedor_insercao.cnpj = digitos;
      return;
    }

    if (digitos.length <= 5) {
      this.fornecedor_insercao.cnpj = `${digitos.slice(0, 2)}.${digitos.slice(2)}`;
      return;
    }

    if (digitos.length <= 8) {
      this.fornecedor_insercao.cnpj = `${digitos.slice(0, 2)}.${digitos.slice(2, 5)}.${digitos.slice(5)}`;
      return;
    }

    if (digitos.length <= 12) {
      this.fornecedor_insercao.cnpj = `${digitos.slice(0, 2)}.${digitos.slice(2, 5)}.${digitos.slice(5, 8)}/${digitos.slice(8)}`;
      return;
    }

    this.fornecedor_insercao.cnpj = `${digitos.slice(0, 2)}.${digitos.slice(2, 5)}.${digitos.slice(5, 8)}/${digitos.slice(8, 12)}-${digitos.slice(12, 14)}`;
  }

  onLogradouroInput(): void {
    this.endereco_insercao.lagradouro = this.limitarTexto(this.endereco_insercao.lagradouro, 255);
  }

  onCepInput(): void {
    const digitos = this.limparNumero(this.endereco_insercao.cep).slice(0, 8);
    if (digitos.length <= 5) {
      this.endereco_insercao.cep = digitos;
      return;
    }

    this.endereco_insercao.cep = `${digitos.slice(0, 5)}-${digitos.slice(5)}`;
  }

  onNumeroEnderecoInput(): void {
    this.endereco_insercao.numero = this.limitarTexto(this.endereco_insercao.numero, 20);
  }

  onBairroInput(): void {
    this.endereco_insercao.bairro = this.limitarTexto(this.endereco_insercao.bairro, 100);
  }

  onMunicipioInput(): void {
    this.endereco_insercao.municipio = this.limitarTexto(this.endereco_insercao.municipio, 100);
  }

  onEstadoInput(): void {
    this.endereco_insercao.estado = (this.endereco_insercao.estado || '')
      .replace(/[^a-zA-Z]/g, '')
      .toUpperCase()
      .slice(0, 2);
  }

  onTelefoneInput(): void {
    const digitos = this.limparNumero(this.fornecedor_insercao.telefone).slice(0, 11);

    if (digitos.length === 0) {
      this.fornecedor_insercao.telefone = '';
      return;
    }

    if (digitos.length <= 2) {
      this.fornecedor_insercao.telefone = `(${digitos}`;
      return;
    }

    const ddd = digitos.slice(0, 2);
    const restante = digitos.slice(2);

    if (digitos.length <= 10) {
      if (restante.length <= 4) {
        this.fornecedor_insercao.telefone = `(${ddd}) ${restante}`;
        return;
      }
      this.fornecedor_insercao.telefone = `(${ddd}) ${restante.slice(0, 4)}-${restante.slice(4)}`;
      return;
    }

    if (restante.length <= 5) {
      this.fornecedor_insercao.telefone = `(${ddd}) ${restante}`;
      return;
    }

    this.fornecedor_insercao.telefone = `(${ddd}) ${restante.slice(0, 5)}-${restante.slice(5)}`;
  }

  onEmailInput(): void {
    this.fornecedor_insercao.email = this.limitarTexto(this.fornecedor_insercao.email, 255);
  }

  onNumeroAtaInput(): void {
    this.ata_insercao.numero_ata = this.limitarTexto(this.ata_insercao.numero_ata, 50);
  }

  onCodigoEmpenhoInput(): void {
    this.empenho_insercao.codigo = this.limitarTexto(this.empenho_insercao.codigo, 50);
  }

  get cnpjValido(): boolean {
    return this.limparNumero(this.fornecedor_insercao.cnpj).length === 14;
  }

  get emailValido(): boolean {
    const email = (this.fornecedor_insercao.email || '').trim();
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  get telefoneValido(): boolean {
    const telefone = this.limparNumero(this.fornecedor_insercao.telefone);
    return telefone.length >= 10 && telefone.length <= 11;
  }

  get cepValido(): boolean {
    return this.limparNumero(this.endereco_insercao.cep).length === 8;
  }

  get estadoValido(): boolean {
    return (this.endereco_insercao.estado || '').trim().length === 2;
  }

  get fornecedorFormValido(): boolean {
    return Boolean(
      this.fornecedor_insercao.razao_social?.trim() &&
      this.fornecedor_insercao.nome_fantasia?.trim() &&
      this.cnpjValido &&
      this.endereco_insercao.lagradouro?.trim() &&
      this.cepValido &&
      this.endereco_insercao.numero?.trim() &&
      this.endereco_insercao.bairro?.trim() &&
      this.endereco_insercao.municipio?.trim() &&
      this.estadoValido &&
      this.telefoneValido &&
      this.emailValido
    );
  }

  get dadosFornecedorPreenchidos(): boolean {
    return Boolean(
      this.fornecedor_insercao.razao_social ||
      this.fornecedor_insercao.nome_fantasia ||
      this.fornecedor_insercao.cnpj ||
      this.endereco_insercao.lagradouro ||
      this.endereco_insercao.cep ||
      this.endereco_insercao.numero ||
      this.endereco_insercao.bairro ||
      this.endereco_insercao.municipio ||
      this.endereco_insercao.estado ||
      this.fornecedor_insercao.telefone ||
      this.fornecedor_insercao.email
    );
  }

  get ataFormValido(): boolean {
    return Boolean(
      this.ata_insercao.numero_ata?.trim() &&
      this.empenho_insercao.codigo?.trim()
    );
  }

  get possuiDadosModalPreenchidos(): boolean {
    return this.dadosFornecedorPreenchidos ||
      Boolean(this.ata_insercao.numero_ata || this.empenho_insercao.codigo || this.fornecedor_insercao.id);
  }

  get podeConcluirCadastro(): boolean {
    return !this.isSaving && this.ataFormValido && (this.jump_page || this.fornecedorFormValido);
  }

  private salvarAtaEEmpenho(): void {
    this.ataService.save(this.ata_insercao).subscribe({
      next: (resposta: AtaInsert) => {
        this.empenho_insercao.ata = resposta.id;
        this.empenhoService.save(this.empenho_insercao).subscribe({
          complete: () => {
            alert('Ata cadastrada com sucesso!');
            window.location.reload();
          },
          error: () => {
            this.isSaving = false;
            this.errorMessageModal = 'Não foi possível concluir o cadastro do empenho. Tente novamente.';
          }
        });
      },
      error: () => {
        this.isSaving = false;
        this.errorMessageModal = 'Não foi possível salvar a ata. Verifique os dados e tente novamente.';
      }
    });
  }


  ngOnInit() {

    const id = this.route.snapshot.queryParamMap.get('id');

    if (id) {
      this.get(Number(id));
      this.getFornecedores();
      this.ata_insercao.licitacao = Number(id);
      this.carregarFornecedoresLicitados(Number(id));
    }
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
        const desejaSair = confirm('Você já preencheu dados da ata. Se sair agora, perderá toda a operação. Deseja sair mesmo assim?');
        if (!desejaSair) {
          event.preventDefault();
        }
      }

    });

  }

  enviarPara(rota: string, id?: number): void {
    if (id) {
      this.router.navigate([rota], { queryParams: { id } });
    }
    else {
      this.router.navigate([rota]);
    }
  }

  get(id: number): void {
    this.licitacaoService.getById(id).subscribe({
      next: (resposta: Licitacao) => {
        this.licitacao = resposta;
      },
      complete: () => {
        this.getAtas(this.licitacao.id);
      }
    });
  }

  getAtas(licitacaoId: number): void {
    this.ataService.getByLicicao(String(licitacaoId), this.currentPageAtas, this.pageSizeAtas).subscribe({
      next: (resposta) => {
        this.atas = resposta.results;
        this.totalAtas = resposta.count;
        this.hasNextAtas = Boolean(resposta.next);
        this.hasPrevAtas = Boolean(resposta.previous);
      }
    });
  }

  private carregarFornecedoresLicitados(licitacaoId: number, page: number = 1): void {
    this.ataService.getByLicicao(String(licitacaoId), page, 100).subscribe({
      next: (resposta) => {
        resposta.results.forEach((ata) => {
          if (!this.fornecedores_licitados.includes(ata.fornecedor.id)) {
            this.fornecedores_licitados.push(ata.fornecedor.id);
          }
        });

        if (resposta.next) {
          this.carregarFornecedoresLicitados(licitacaoId, page + 1);
        }
      }
    });
  }

  getFornecedores(termobusca?: string): void {
    if (termobusca !== undefined) {
      this.termoBuscaFornecedor = termobusca;
      this.currentPageFornecedores = 1;
    }

    this.fornecedorService.get(this.termoBuscaFornecedor, this.currentPageFornecedores, this.pageSizeFornecedores).subscribe({
      next: (resposta) => {
        this.fornecedores = resposta.results;
        this.totalFornecedores = resposta.count;
        this.hasNextFornecedores = Boolean(resposta.next);
        this.hasPrevFornecedores = Boolean(resposta.previous);
      }
    });
  }

  proximaPaginaAtas(): void {
    if (!this.hasNextAtas) {
      return;
    }

    this.currentPageAtas += 1;
    this.getAtas(this.licitacao.id);
  }

  paginaAnteriorAtas(): void {
    if (!this.hasPrevAtas || this.currentPageAtas === 1) {
      return;
    }

    this.currentPageAtas -= 1;
    this.getAtas(this.licitacao.id);
  }

  irParaPaginaAtas(page: number): void {
    if (page === this.currentPageAtas) {
      return;
    }

    this.currentPageAtas = page;
    this.getAtas(this.licitacao.id);
  }

  proximaPaginaFornecedores(): void {
    if (!this.hasNextFornecedores) {
      return;
    }

    this.currentPageFornecedores += 1;
    this.getFornecedores();
  }

  paginaAnteriorFornecedores(): void {
    if (!this.hasPrevFornecedores || this.currentPageFornecedores === 1) {
      return;
    }

    this.currentPageFornecedores -= 1;
    this.getFornecedores();
  }

  irParaPaginaFornecedores(page: number): void {
    if (page === this.currentPageFornecedores) {
      return;
    }

    this.currentPageFornecedores = page;
    this.getFornecedores();
  }

  escolherFornecedor(fornecedor: Fornecedor): void {
    this.ata_insercao.fornecedor = fornecedor.id;
    this.fornecedor_insercao.id = fornecedor.id;
    this.fornecedor_insercao.cnpj = fornecedor.cnpj;
    this.fornecedor_insercao.email = fornecedor.email;
    this.fornecedor_insercao.nome_fantasia = fornecedor.nome_fantasia;
    this.fornecedor_insercao.razao_social = fornecedor.razao_social;
    this.fornecedor_insercao.telefone = fornecedor.telefone;
    this.endereco_insercao = fornecedor.endereco;
    this.jump_page = true;
    this.avanca_modal_page(2);
  }

  avanca_modal_page(valor?: number): void {
    if (this.isSaving) {
      return;
    }

    if (this.modal_page === 1 && valor === undefined) {
      this.formSubmittedPage1 = true;
      if (!this.fornecedorFormValido) {
        return;
      }
    }

    this.modal_page = valor !== undefined ? valor : this.modal_page + 1;
  }

  volta_modal_page(valor?: number): void {
    if (this.isSaving) {
      return;
    }

    this.modal_page = valor !== undefined ? valor : this.modal_page - 1;
    if (this.jump_page == true) {
      this.jump_page = false;
      this.fornecedor_insercao = <FornecedorInsert>{};
      this.endereco_insercao = <Endereco>{};
    }
  }

  reiniciar_Modal(): void {
    if (this.isSaving) {
      return;
    }

    this.modal_page = 0;
    this.jump_page = false;
    this.formSubmittedPage1 = false;
    this.formSubmittedPage2 = false;
    this.errorMessageModal = '';
    this.fornecedor_insercao = <FornecedorInsert>{};
    this.endereco_insercao = <Endereco>{};
    this.ata_insercao.numero_ata = '';
    this.empenho_insercao.codigo = '';
  }

  saveAta(): void {
    this.formSubmittedPage2 = true;
    this.errorMessageModal = '';

    if (this.isSaving || !this.ataFormValido) {
      return;
    }

    this.isSaving = true;

    this.ata_insercao.numero_ata = this.ata_insercao.numero_ata?.trim().toUpperCase();
    this.empenho_insercao.codigo = this.empenho_insercao.codigo?.trim().toUpperCase();

    this.salvarAtaEEmpenho();
  }

  saveFornecedor(): void {
    this.formSubmittedPage1 = true;
    this.formSubmittedPage2 = true;
    this.errorMessageModal = '';

    if (this.isSaving || !this.fornecedorFormValido || !this.ataFormValido) {
      return;
    }

    this.isSaving = true;
    this.fornecedor_insercao.razao_social = this.fornecedor_insercao.razao_social?.trim();
    this.fornecedor_insercao.nome_fantasia = this.fornecedor_insercao.nome_fantasia?.trim();
    this.fornecedor_insercao.cnpj = this.limparNumero(this.fornecedor_insercao.cnpj);
    this.fornecedor_insercao.telefone = this.limparNumero(this.fornecedor_insercao.telefone);
    this.fornecedor_insercao.email = this.fornecedor_insercao.email?.trim();
    this.endereco_insercao.cep = this.limparNumero(this.endereco_insercao.cep);
    this.endereco_insercao.estado = this.endereco_insercao.estado?.trim().toUpperCase();
    this.ata_insercao.numero_ata = this.ata_insercao.numero_ata?.trim().toUpperCase();
    this.empenho_insercao.codigo = this.empenho_insercao.codigo?.trim().toUpperCase();

    this.enderecoService.save(this.endereco_insercao).subscribe({
      next: (resposta: Endereco) => {
        this.fornecedor_insercao.endereco = resposta.id;
        this.fornecedorService.save(this.fornecedor_insercao).subscribe({
          next: (resposta: FornecedorInsert) => {
            this.ata_insercao.fornecedor = resposta.id;
          },
          complete: () => {
            this.salvarAtaEEmpenho();
          },
          error: () => {
            this.isSaving = false;
            this.errorMessageModal = 'Não foi possível salvar o fornecedor. Verifique os dados e tente novamente.';
          }
        });
      },
      error: () => {
        this.isSaving = false;
        this.errorMessageModal = 'Não foi possível salvar o endereço. Verifique os dados e tente novamente.';
      }
    });
  }

  tentarFecharModal(): void {
    if (this.isSaving) {
      return;
    }

    if (this.possuiDadosModalPreenchidos) {
      const desejaSair = confirm('Você já preencheu dados da ata. Se sair agora, perderá toda a operação. Deseja sair mesmo assim?');
      if (!desejaSair) {
        return;
      }
    }

    if (this.fecharModalInternoBtn?.nativeElement) {
      this.permitirFecharModalSemConfirmacao = true;
      this.fecharModalInternoBtn.nativeElement.click();
    }
  }
}

