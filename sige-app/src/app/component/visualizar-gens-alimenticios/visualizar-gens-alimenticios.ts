import { FiltroConfig } from './../../model/filtro-config';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { BarraPesquisa } from '../utils/barra-pesquisa/barra-pesquisa';
import { Router } from '@angular/router';
import { ItemGenericoService } from '../../service/item-generico.service';
import { ItemGenerico } from '../../model/item_generico';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-visualizar-gens-alimenticios',
  imports: [BarraPesquisa, FormsModule],
  templateUrl: './visualizar-gens-alimenticios.html',
  styleUrl: './visualizar-gens-alimenticios.scss',
})
export class VisualizarGensAlimenticios {

  @ViewChild('myModal') modal!: ElementRef;
  @ViewChild('myInput') input!: ElementRef;

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
    private router: Router
  ) { }

  registros: ItemGenerico[] = [];
  registroEditar: ItemGenerico = <ItemGenerico>{};

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

    const params = { ...this.filtrosAtivos };

    if (termobusca) {
      params['search'] = termobusca;
    }

    this.ItemGenericoService.getComFiltros(params).subscribe(
      (registro: ItemGenerico[]) => {
        this.registros = registro;
      }
    );

  }

  ngOnInit() {
    this.getItens();

    this.filtros[0].opcoes = this.categoriasDisponiveis.map(cat => ({
      id: cat,
      nome: this.getCategoriaLabel(cat)
    }));

    this.filtros[1].opcoes = this.unidadesDisponiveis.map(un => ({
      id: un,
      nome: this.getUnidadeMedidaLabel(un)
    }));
  }

  enviarPara(rota: string, id?: number) {
    if (id) {
      this.router.navigate([rota], { queryParams: { id } });
    }
    else {
      this.router.navigate([rota]);
    }
  }

  carregarRegistro(registro: ItemGenerico) {
    this.registroEditar = { ...registro };
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
    this.ItemGenericoService.save(this.registroEditar).subscribe({
      next: () => {
        window.location.reload();
      }
    });
  }

  aplicarFiltros(filtros: any) {
    this.filtrosAtivos = filtros;
    this.getItens();
  }

}
