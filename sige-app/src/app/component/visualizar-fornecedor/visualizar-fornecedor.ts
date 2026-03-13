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

@Component({
  selector: 'app-visualizar-fornecedor',
  imports: [BotaoVoltar, FormsModule],
  templateUrl: './visualizar-fornecedor.html',
  styleUrl: './visualizar-fornecedor.scss',
})
export class VisualizarFornecedor {

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild("myInput") input!: ElementRef;

  constructor(
    private fornecedorService: FornecedorService,
    private enderecoService: EnderecoService,
    private route: ActivatedRoute,
    private router: Router
  ) { }


  fornecedor = <Fornecedor>{};
  fornecedor_editar = <FornecedorInsert>{};
  endereco_editar = <Endereco>{};


  ngOnInit() {
    const id = this.route.snapshot.queryParamMap.get('id');

    if (id) {
      this.get(Number(id))
    }
  }

  ngAfterViewInit() {

    const modalElement = this.modal.nativeElement;

    modalElement.addEventListener('shown.bs.modal', () => {

      this.input.nativeElement.focus();

    });

  }

  carregar_Fornecedor() {
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

  get(id: number): void {
    this.fornecedorService.getById(id).subscribe(
      {
        next: (reposta: Fornecedor) => {
          this.fornecedor = reposta
        }
      }
    )
  }

  saveFornecedo(): void {
      this.fornecedorService.save(this.fornecedor_editar).subscribe(
        {
          complete: () => {
            alert('Fornecedor editado com sucesso!');
            window.location.reload();
          }
        }
      )
  }

  save(): void {
    this.enderecoService.save(this.endereco_editar).subscribe(
      {
        complete: () => {
          this.saveFornecedo();
        }
      }
    )
  }
}
