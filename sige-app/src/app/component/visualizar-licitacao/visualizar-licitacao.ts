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
import { AtaInsert } from '../../model/ata_insert';
import { FornecedorInsert } from '../../model/fornecedor_insert';
import { EnderecoService } from '../../service/endereco.service';
import { EmpenhoInsert } from '../../model/empenho_insert';
import { EmpenhoService } from '../../service/empenho.service';

@Component({
  selector: 'app-visualizar-licitacao',
  imports: [CommonModule, BotaoVoltar, FormsModule, BarraPesquisa],
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

  licitacao: Licitacao = <Licitacao>{};
  atas: Array<Ata> = Array<Ata>();
  fornecedores: Fornecedor[] = [];
  fornecedores_licitados: number[] = [];

  fornecedor_insercao: FornecedorInsert = <FornecedorInsert>{};
  endereco_insercao: Endereco = <Endereco>{};
  ata_insercao: AtaInsert = <AtaInsert>{ ata_saldo_total: 0 };
  empenho_insercao: EmpenhoInsert = <EmpenhoInsert>{ saldo_utilizado: 0, quantidade_itens: 0, valor_total: 0 };

  modal_page: number = 0;
  jump_page: boolean = false;


  ngOnInit() {

    const id = this.route.snapshot.queryParamMap.get('id');

    if (id) {
      this.get(Number(id));
      this.getFornecedores();
      this.ata_insercao.licitacao = Number(id);
    }
  }

  ngAfterViewInit() {

    const modalElement = this.modal.nativeElement;

    modalElement.addEventListener('shown.bs.modal', () => {

      this.input.nativeElement.focus();

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
    this.ataService.getByLicicao(String(licitacaoId)).subscribe({
      next: (resposta: Array<Ata>) => {
        this.atas = resposta;
      },
      complete: () => {
        this.atas.forEach(ata => {
          this.fornecedores_licitados.push(ata.fornecedor.id);
        });
      }
    });
  }

  getFornecedores(): void {
    this.fornecedorService.get().subscribe({
      next: (resposta: Fornecedor[]) => {
        this.fornecedores = resposta;
      }
    });
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
    this.modal_page = valor !== undefined ? valor : this.modal_page + 1;
  }

  volta_modal_page(valor?: number): void {
    this.modal_page = valor !== undefined ? valor : this.modal_page - 1;
    if (this.jump_page == true) {
      this.jump_page = false;
      this.fornecedor_insercao = <FornecedorInsert>{};
      this.endereco_insercao = <Endereco>{};
    }
  }

  reiniciar_Modal(): void {
    this.modal_page = 0;
    this.jump_page = false;
    this.fornecedor_insercao = <FornecedorInsert>{};
    this.endereco_insercao = <Endereco>{};
  }

  saveAta(): void {
    this.ataService.save(this.ata_insercao).subscribe({
      next: (resposta: AtaInsert) => {
        this.empenho_insercao.ata = resposta.id;
        this.empenhoService.save(this.empenho_insercao).subscribe({
          complete: () => {
            alert('Ata cadastrada com sucesso!');
            window.location.reload();
          }
        });
      }
    });
  }

  saveFornecedor(): void {
    this.enderecoService.save(this.endereco_insercao).subscribe({
      next: (resposta: Endereco) => {
        this.fornecedor_insercao.endereco = resposta.id;
        this.fornecedorService.save(this.fornecedor_insercao).subscribe({
          next: (resposta: FornecedorInsert) => {
            this.ata_insercao.fornecedor = resposta.id;
          },
          complete: () => {
            this.saveAta();
          }
        });
      }
    });
  }
}

