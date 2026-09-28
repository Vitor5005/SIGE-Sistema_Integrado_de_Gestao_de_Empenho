import { FiltroConfig } from './../../../model/filtro-config';
import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { Subject } from 'rxjs';
import { debounceTime } from 'rxjs/internal/operators/debounceTime';
import { distinctUntilChanged } from 'rxjs/internal/operators/distinctUntilChanged';

interface FiltroAtivoChip {
  id: string;
  label: string;
  campo: string;
  campos: string[];
  tipo: 'checkbox' | 'valor' | 'intervalo';
  valor?: any;
}

@Component({
  selector: 'app-barra-pesquisa',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './barra-pesquisa.html',
  styleUrl: './barra-pesquisa.scss',
})
export class BarraPesquisa implements OnInit, OnChanges {
  @Input() filtros: FiltroConfig[] = [];
  @Input() placeholder = 'Pesquisar...';
  @Input() termoInicial = '';
  @Input() valoresIniciais: Record<string, any> = {};

  @Output() pesquisar = new EventEmitter<string>();
  @Output() filtrosAlterados = new EventEmitter<any>();

  private searchSubject = new Subject<string>();

  valores: Record<string, any> = {};
  termoBusca = '';

  filtrosLicitacoes: FiltroConfig[] = [
    {
      campo: 'data_abertura',
      label: 'Período da venda',
      tipo: 'date-range'
    }
  ];

  ngOnInit(): void {
    this.searchSubject.pipe(debounceTime(300), distinctUntilChanged()).subscribe((termo) => {
      this.pesquisar.emit(termo);
    });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['termoInicial']) {
      this.termoBusca = this.termoInicial ?? '';
    }

    if (changes['valoresIniciais']) {
      this.valores = this.copiarValores(this.valoresIniciais);
    }
  }

  onPesquisar(event: Event): void {
    const termo = (event.target as HTMLInputElement).value;
    this.termoBusca = termo;
    this.searchSubject.next(termo);
  }

  alterarFiltro(campo: string, valor: any, evento?: Event): void {
    const checkbox = evento?.target as HTMLInputElement;

    if (checkbox && checkbox.type === 'checkbox') {
      const valoresSelecionados = Array.isArray(this.valores[campo])
        ? [...this.valores[campo]]
        : [];

      if (checkbox.checked) {
        if (!valoresSelecionados.some((valorSelecionado) => valorSelecionado === valor)) {
          valoresSelecionados.push(valor);
        }
      } else {
        this.valores[campo] = valoresSelecionados.filter((valorSelecionado) => valorSelecionado !== valor);
      }

      if (checkbox.checked) {
        this.valores[campo] = valoresSelecionados;
      }

      if (this.valores[campo]?.length === 0) {
        delete this.valores[campo];
      }
    } else {
      if (valor === null || valor === undefined || valor === '') {
        delete this.valores[campo];
      } else {
        this.valores[campo] = valor;
      }
    }

    this.emitirFiltros();
  }

  limparFiltros(): void {
    this.filtros.forEach((filtro) => {
      delete this.valores[filtro.campo];
      delete this.valores[`${filtro.campo}__gte`];
      delete this.valores[`${filtro.campo}__lte`];
    });

    this.emitirFiltros();
  }

  get chipsAtivos(): FiltroAtivoChip[] {
    return this.filtros.flatMap((filtro) => this.criarChipsDoFiltro(filtro));
  }

  removerFiltro(chip: FiltroAtivoChip): void {
    if (chip.tipo === 'checkbox') {
      const valoresSelecionados = Array.isArray(this.valores[chip.campo])
        ? this.valores[chip.campo].filter((valor: any) => valor !== chip.valor)
        : [];

      if (valoresSelecionados.length > 0) {
        this.valores[chip.campo] = valoresSelecionados;
      } else {
        delete this.valores[chip.campo];
      }
    } else {
      chip.campos.forEach((campo) => delete this.valores[campo]);
    }

    this.emitirFiltros();
  }

  valorOpcao(opcao: any): any {
    return opcao?.valor ?? opcao?.id ?? opcao;
  }

  rotuloOpcao(opcao: any): string {
    const valor = opcao?.label ?? opcao?.nome ?? opcao?.numero ?? opcao?.valor ?? opcao?.id ?? opcao;
    return valor === null || valor === undefined ? '' : String(valor);
  }

  opcaoMarcada(campo: string, valor: any): boolean {
    return Array.isArray(this.valores[campo]) && this.valores[campo].some((valorSelecionado: any) => this.mesmoValor(valorSelecionado, valor));
  }

  valorSelecionado(campo: string): any {
    return this.valores[campo] ?? '';
  }

  mesmoValor(valorAtual: any, valorComparado: any): boolean {
    return String(valorAtual) === String(valorComparado);
  }

  private criarChipsDoFiltro(filtro: FiltroConfig): FiltroAtivoChip[] {
    const tipo = filtro.tipo;
    const campo = filtro.campo;

    if (tipo === 'range' || tipo === 'date-range') {
      const campoInicial = `${campo}__gte`;
      const campoFinal = `${campo}__lte`;
      const valorInicial = this.valores[campoInicial];
      const valorFinal = this.valores[campoFinal];

      if (!this.temValor(valorInicial) && !this.temValor(valorFinal)) {
        return [];
      }

      return [{
        id: `${campo}:intervalo`,
        label: this.rotuloIntervalo(filtro.label, valorInicial, valorFinal, tipo === 'date-range'),
        campo,
        campos: [campoInicial, campoFinal],
        tipo: 'intervalo'
      }];
    }

    if (tipo === 'checkbox') {
      const valoresSelecionados = Array.isArray(this.valores[campo]) ? this.valores[campo] : [];
      return valoresSelecionados.map((valor) => ({
        id: `${campo}:${String(valor)}`,
        label: `${filtro.label}: ${this.rotuloValor(filtro, valor)}`,
        campo,
        campos: [campo],
        tipo: 'checkbox' as const,
        valor
      }));
    }

    const valor = this.valores[campo];
    if (!this.temValor(valor)) {
      return [];
    }

    return [{
      id: `${campo}:${String(valor)}`,
      label: `${filtro.label}: ${this.rotuloValor(filtro, valor)}`,
      campo,
      campos: [campo],
      tipo: 'valor'
    }];
  }

  private rotuloValor(filtro: FiltroConfig, valor: any): string {
    const opcao = ((filtro as any).opcoes ?? []).find((item: any) => this.mesmoValor(this.valorOpcao(item), valor));
    return opcao ? this.rotuloOpcao(opcao) : String(valor);
  }

  private rotuloIntervalo(label: string, inicio: any, fim: any, formatarData: boolean): string {
    const possuiInicio = this.temValor(inicio);
    const possuiFim = this.temValor(fim);

    if (!formatarData) {
      if (possuiInicio && possuiFim) {
        return `${label}: ${this.formatarIntervalo(inicio, false)} – ${this.formatarIntervalo(fim, false)}`;
      }

      if (possuiInicio) {
        return `${label}: mín. ${this.formatarIntervalo(inicio, false)}`;
      }

      return `${label}: máx. ${this.formatarIntervalo(fim, false)}`;
    }

    const valores = [
      possuiInicio ? `De ${this.formatarIntervalo(inicio, true)}` : '',
      possuiFim ? `Até ${this.formatarIntervalo(fim, true)}` : ''
    ].filter(Boolean);

    return `${label}: ${valores.join(' · ')}`;
  }

  private formatarIntervalo(valor: any, formatarData: boolean): string {
    const valorTexto = String(valor);
    if (formatarData && /^\d{4}-\d{2}-\d{2}$/.test(valorTexto)) {
      const [ano, mes, dia] = valorTexto.split('-');
      return `${dia}/${mes}/${ano}`;
    }

    return valorTexto;
  }

  private temValor(valor: any): boolean {
    return valor !== null && valor !== undefined && valor !== '';
  }

  private copiarValores(valores: Record<string, any> | null | undefined): Record<string, any> {
    return Object.entries(valores ?? {}).reduce((copia, [campo, valor]) => {
      copia[campo] = Array.isArray(valor) ? [...valor] : valor;
      return copia;
    }, {} as Record<string, any>);
  }

  private emitirFiltros(): void {
    this.filtrosAlterados.emit(this.valores);
  }
}
