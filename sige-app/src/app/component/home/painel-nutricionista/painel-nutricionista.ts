import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import {
  DisponibilidadeGenero,
  PainelNutricionista as DadosPainel,
  SaldoArp,
  SaldoEmpenho,
} from '../../../model/painel_nutricionista';
import { PainelNutricionistaService } from '../../../service/painel-nutricionista.service';

type Etapa = 'em_estoque' | 'a_caminho' | 'empenhado' | 'na_arp';

interface Situacao {
  rotulo: string;
  icone: string;
  tipo: 'bom' | 'neutro' | 'critico';
}

interface Dica {
  x: number;
  y: number;
  titulo: string;
  linhas: { chave: string; rotulo: string; valor: string }[];
}

interface GrupoEstoque {
  unidade: string;
  maximo: number;
  itens: DisponibilidadeGenero[];
}

interface Medidor {
  id: number;
  titulo: string;
  subtitulo: string;
  total: number;
  disponivel: number;
}

// Do mais imediato ao mais distante: a ordem define a rampa de cor (escuro = pode usar já).
export const ETAPAS: { chave: Etapa; rotulo: string; descricao: string }[] = [
  { chave: 'em_estoque', rotulo: 'Em estoque', descricao: 'Pode usar agora' },
  { chave: 'a_caminho', rotulo: 'A caminho', descricao: 'Ordem emitida, aguardando entrega' },
  { chave: 'empenhado', rotulo: 'Empenhado', descricao: 'Já empenhado; falta emitir a ordem de entrega' },
  { chave: 'na_arp', rotulo: 'Na ARP', descricao: 'Registrado na ata; falta empenhar' },
];

const LARGURA_GRAFICO = 640;
const ALTURA_GRAFICO = 220;
const MARGEM = { topo: 12, direita: 8, base: 28, esquerda: 56 };
const ITENS_POR_UNIDADE = 8;
const GENEROS_NA_TABELA = 10;

@Component({
  selector: 'app-painel-nutricionista',
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './painel-nutricionista.html',
  styleUrl: './painel-nutricionista.scss',
})
export class PainelNutricionista implements OnInit {
  readonly etapas = ETAPAS;
  readonly largura = LARGURA_GRAFICO;
  readonly altura = ALTURA_GRAFICO;
  readonly margem = MARGEM;

  dados: DadosPainel | null = null;
  carregando = true;
  erro = false;

  busca = '';
  categoria = '';
  tabelaCompleta = false;
  generoMovimentoId: string | null = null;
  unidadesExpandidas = new Set<string>();
  dica: Dica | null = null;

  private readonly numero = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 3 });
  private readonly moeda = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

  constructor(private painelService: PainelNutricionistaService) {}

  ngOnInit(): void {
    this.carregar();
  }

  carregar(): void {
    this.carregando = true;
    this.erro = false;
    this.painelService.carregar().subscribe({
      next: (dados) => {
        this.dados = dados;
        this.carregando = false;
        this.generoMovimentoId = this.generoComMaisMovimento();
      },
      error: () => {
        this.erro = true;
        this.carregando = false;
      },
    });
  }

  // ---- Indicadores ----

  get generos(): DisponibilidadeGenero[] {
    return this.dados?.generos ?? [];
  }

  get quantidadeEmEstoque(): number {
    return this.generos.filter((g) => +g.em_estoque > 0).length;
  }

  get quantidadeACaminho(): number {
    return this.generos.filter((g) => +g.a_caminho > 0).length;
  }

  get saldoEmpenhos(): number {
    return (this.dados?.empenhos ?? []).reduce((total, e) => total + +e.saldo_disponivel, 0);
  }

  get saldoArps(): number {
    return (this.dados?.arps ?? []).reduce((total, a) => total + +a.saldo_disponivel, 0);
  }

  // ---- O que posso usar no cardápio ----

  get categorias(): { valor: string; rotulo: string }[] {
    const vistas = new Map<string, string>();
    this.generos.forEach((g) => vistas.set(g.categoria, g.categoria_descricao));
    return [...vistas].map(([valor, rotulo]) => ({ valor, rotulo }));
  }

  get generosFiltrados(): DisponibilidadeGenero[] {
    const termo = this.busca.trim().toLowerCase();
    return this.generos.filter((g) =>
      (!this.categoria || g.categoria === this.categoria)
      && (!termo || g.descricao.toLowerCase().includes(termo) || g.catmat.includes(termo)),
    );
  }

  get generosVisiveis(): DisponibilidadeGenero[] {
    return this.tabelaCompleta ? this.generosFiltrados : this.generosFiltrados.slice(0, GENEROS_NA_TABELA);
  }

  get generosOcultos(): number {
    return Math.max(0, this.generosFiltrados.length - GENEROS_NA_TABELA);
  }

  totalDisponivel(genero: DisponibilidadeGenero): number {
    return this.etapas.reduce((total, etapa) => total + +genero[etapa.chave], 0);
  }

  valorEtapa(genero: DisponibilidadeGenero, etapa: Etapa): number {
    return +genero[etapa];
  }

  percentualEtapa(genero: DisponibilidadeGenero, etapa: Etapa): number {
    const total = this.totalDisponivel(genero);
    return total > 0 ? (+genero[etapa] / total) * 100 : 0;
  }

  situacao(genero: DisponibilidadeGenero): Situacao {
    if (+genero.em_estoque > 0) return { rotulo: 'Pronto para uso', icone: 'bi-check-circle-fill', tipo: 'bom' };
    if (+genero.a_caminho > 0) return { rotulo: 'Chegando', icone: 'bi-truck', tipo: 'neutro' };
    if (+genero.empenhado > 0) return { rotulo: 'Pedir entrega', icone: 'bi-receipt', tipo: 'neutro' };
    if (+genero.na_arp > 0) return { rotulo: 'Pedir empenho', icone: 'bi-journal-text', tipo: 'neutro' };
    return { rotulo: 'Indisponível', icone: 'bi-x-octagon-fill', tipo: 'critico' };
  }

  // ---- Estoque atual (um gráfico por unidade: KG e UN não se comparam na mesma escala) ----

  get gruposEstoque(): GrupoEstoque[] {
    const grupos = new Map<string, DisponibilidadeGenero[]>();
    this.generos
      .filter((g) => +g.em_estoque > 0)
      .forEach((g) => grupos.set(g.unidade_medida, [...(grupos.get(g.unidade_medida) ?? []), g]));
    return [...grupos].map(([unidade, itens]) => {
      const ordenados = itens.sort((a, b) => +b.em_estoque - +a.em_estoque);
      return { unidade, maximo: +ordenados[0].em_estoque, itens: ordenados };
    });
  }

  itensVisiveis(grupo: GrupoEstoque): DisponibilidadeGenero[] {
    return this.unidadesExpandidas.has(grupo.unidade) ? grupo.itens : grupo.itens.slice(0, ITENS_POR_UNIDADE);
  }

  larguraEstoque(genero: DisponibilidadeGenero, grupo: GrupoEstoque): number {
    return grupo.maximo > 0 ? (+genero.em_estoque / grupo.maximo) * 100 : 0;
  }

  alternarUnidade(unidade: string): void {
    if (this.unidadesExpandidas.has(unidade)) {
      this.unidadesExpandidas.delete(unidade);
    } else {
      this.unidadesExpandidas.add(unidade);
    }
  }

  // ---- Entradas e saídas por semana ----

  get generosComMovimento(): DisponibilidadeGenero[] {
    const ids = new Set(Object.keys(this.dados?.movimentacao.por_genero ?? {}));
    return this.generos.filter((g) => ids.has(String(g.item_generico_id)));
  }

  get generoMovimento(): DisponibilidadeGenero | undefined {
    return this.generos.find((g) => String(g.item_generico_id) === this.generoMovimentoId);
  }

  get semanas(): string[] {
    return this.dados?.movimentacao.semanas ?? [];
  }

  get entradas(): number[] {
    return this.serie('entradas');
  }

  get saidas(): number[] {
    return this.serie('saidas');
  }

  get maximoMovimento(): number {
    return this.escalaRedonda(Math.max(0, ...this.entradas, ...this.saidas));
  }

  get ticksMovimento(): number[] {
    const maximo = this.maximoMovimento;
    return [0, maximo / 4, maximo / 2, (maximo * 3) / 4, maximo];
  }

  get larguraGrupo(): number {
    return (LARGURA_GRAFICO - MARGEM.esquerda - MARGEM.direita) / Math.max(this.semanas.length, 1);
  }

  get larguraColuna(): number {
    return Math.min(24, this.larguraGrupo * 0.3);
  }

  yValor(valor: number): number {
    const alturaPlot = ALTURA_GRAFICO - MARGEM.topo - MARGEM.base;
    return MARGEM.topo + alturaPlot - (valor / (this.maximoMovimento || 1)) * alturaPlot;
  }

  xGrupo(indice: number): number {
    return MARGEM.esquerda + indice * this.larguraGrupo;
  }

  /** Coluna com topo arredondado (4px) e base reta, crescendo da linha de base. */
  caminhoColuna(indice: number, valor: number, serie: 0 | 1): string {
    const baseY = this.yValor(0);
    const topoY = this.yValor(valor);
    const altura = baseY - topoY;
    if (altura <= 0) return '';
    const largura = this.larguraColuna;
    const centro = this.xGrupo(indice) + this.larguraGrupo / 2;
    const x = serie === 0 ? centro - largura - 1 : centro + 1;
    const raio = Math.min(4, altura, largura / 2);
    return `M${x},${baseY} V${topoY + raio} Q${x},${topoY} ${x + raio},${topoY} `
      + `H${x + largura - raio} Q${x + largura},${topoY} ${x + largura},${topoY + raio} V${baseY} Z`;
  }

  rotuloSemana(semana: string): string {
    const [, mes, dia] = semana.split('-');
    return `${dia}/${mes}`;
  }

  // ---- Saldos financeiros ----

  get medidoresEmpenho(): Medidor[] {
    return (this.dados?.empenhos ?? []).map((e: SaldoEmpenho) => ({
      id: e.id, titulo: e.codigo, subtitulo: e.fornecedor,
      total: +e.valor_total, disponivel: +e.saldo_disponivel,
    })).sort((a, b) => b.disponivel - a.disponivel);
  }

  get medidoresArp(): Medidor[] {
    return (this.dados?.arps ?? []).map((a: SaldoArp) => ({
      id: a.id, titulo: a.numero_ata, subtitulo: `${a.fornecedor} · Licitação ${a.licitacao}`,
      total: +a.valor_registrado, disponivel: +a.saldo_disponivel,
    })).sort((a, b) => b.disponivel - a.disponivel);
  }

  percentualMedidor(medidor: Medidor): number {
    return medidor.total > 0 ? Math.min(100, (medidor.disponivel / medidor.total) * 100) : 0;
  }

  // ---- Dica (tooltip) compartilhada ----

  mostrarDica(evento: MouseEvent | FocusEvent, titulo: string, linhas: Dica['linhas']): void {
    let x: number;
    let y: number;
    if (evento instanceof MouseEvent) {
      x = evento.clientX;
      y = evento.clientY;
    } else {
      const retangulo = (evento.target as Element).getBoundingClientRect();
      x = retangulo.left + retangulo.width / 2;
      y = retangulo.top;
    }
    this.dica = { x, y, titulo, linhas };
  }

  dicaGenero(evento: MouseEvent | FocusEvent, genero: DisponibilidadeGenero): void {
    this.mostrarDica(evento, genero.descricao, this.etapas.map((etapa) => ({
      chave: etapa.chave,
      rotulo: etapa.rotulo,
      valor: this.quantidade(+genero[etapa.chave], genero.unidade_medida),
    })));
  }

  dicaSemana(evento: MouseEvent | FocusEvent, indice: number): void {
    const unidade = this.generoMovimento?.unidade_medida ?? '';
    this.mostrarDica(evento, `Semana de ${this.rotuloSemana(this.semanas[indice])}`, [
      { chave: 'entradas', rotulo: 'Entradas', valor: this.quantidade(this.entradas[indice], unidade) },
      { chave: 'saidas', rotulo: 'Saídas', valor: this.quantidade(this.saidas[indice], unidade) },
    ]);
  }

  esconderDica(): void {
    this.dica = null;
  }

  // ---- Formatação ----

  quantidade(valor: number, unidade: string): string {
    return `${this.numero.format(+valor)} ${unidade}`;
  }

  formatarNumero(valor: number): string {
    return this.numero.format(+valor);
  }

  formatarMoeda(valor: number): string {
    return this.moeda.format(+valor);
  }

  private serie(chave: 'entradas' | 'saidas'): number[] {
    const serie = this.generoMovimentoId ? this.dados?.movimentacao.por_genero[this.generoMovimentoId] : undefined;
    return (serie?.[chave] ?? this.semanas.map(() => 0)).map(Number);
  }

  private generoComMaisMovimento(): string | null {
    const porGenero = this.dados?.movimentacao.por_genero ?? {};
    let melhor: string | null = null;
    let maior = -1;
    for (const [id, serie] of Object.entries(porGenero)) {
      const total = [...serie.entradas, ...serie.saidas].reduce((soma, v) => soma + +v, 0);
      if (total > maior) {
        maior = total;
        melhor = id;
      }
    }
    return melhor;
  }

  /** Arredonda o topo da escala para um número limpo (1, 2, 2,5 ou 5 × 10ⁿ). */
  private escalaRedonda(valor: number): number {
    if (valor <= 0) return 1;
    const potencia = 10 ** Math.floor(Math.log10(valor));
    const passo = [1, 2, 2.5, 5, 10].find((m) => m * potencia >= valor) ?? 10;
    return passo * potencia;
  }
}
