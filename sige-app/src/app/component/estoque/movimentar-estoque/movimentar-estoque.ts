import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Observable } from 'rxjs';

import { EstoqueItem, LoteInventario, LoteSaida } from '../../../model/estoque';
import { EstoqueService } from '../../../service/estoque.service';

type Operacao = 'SAIDA' | 'INVENTARIO' | 'CARGA_INICIAL';

interface LoteCargaInicialForm {
  numero_lote: string;
  data_validade: string;
  quantidade: number | null;
}

interface LoteInventarioForm {
  lote_id?: number;
  numero_lote: string;
  data_validade: string | null;
  saldo_sistema: number;
  quantidade_contada: number | null;
  legado: boolean;
  vencido: boolean;
  novo: boolean;
}

const DESCRICOES: Record<Operacao, string> = {
  SAIDA: 'Retira do estoque o que foi consumido, doado ou perdido.',
  INVENTARIO: 'Informe os lotes encontrados na contagem física.',
  CARGA_INICIAL: 'Registra o saldo que já existia antes do sistema. Feita uma única vez por gênero.',
};

@Component({
  selector: 'app-movimentar-estoque',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './movimentar-estoque.html',
  styleUrl: '../estoque.scss',
})
export class MovimentarEstoque {
  operacao: Operacao = 'SAIDA';
  itens: EstoqueItem[] = [];
  itemGenericoId?: number;
  quantidade?: number;
  tipoSaida = 'PRODUCAO';
  lotesPerda: LoteSaida[] = [];
  loteId?: number;
  carregandoLotes = false;
  lotesCargaInicial: LoteCargaInicialForm[] = [];
  lotesInventario: LoteInventarioForm[] = [];
  carregandoLotesInventario = false;
  justificativa = '';
  dataHora = this.agoraLocalParaInput();
  processando = false;
  erro = '';
  sucesso = '';

  constructor(private estoqueService: EstoqueService) {}

  ngOnInit(): void {
    this.carregarItens();
  }

  get itensSemCargaInicial(): EstoqueItem[] {
    return this.itens.filter(item => !item.possui_carga_inicial);
  }

  get itensDaOperacao(): EstoqueItem[] {
    return this.operacao === 'CARGA_INICIAL' ? this.itensSemCargaInicial : this.itens;
  }

  get itemSelecionado(): EstoqueItem | undefined {
    return this.itens.find(item => item.item_generico_id === this.itemGenericoId);
  }

  get descricaoOperacao(): string {
    return DESCRICOES[this.operacao];
  }

  get totalCargaInicial(): number {
    return this.lotesCargaInicial.reduce((total, lote) => total + this.valorNumero(lote.quantidade), 0);
  }

  get totalContadoInventario(): number {
    return this.lotesInventario.reduce(
      (total, lote) => total + this.valorNumero(lote.quantidade_contada),
      0,
    );
  }

  get diferencaTotalInventario(): number {
    return this.totalContadoInventario - this.valorNumero(this.itemSelecionado?.saldo_atual);
  }

  get inventarioPossuiDiferenca(): boolean {
    return this.lotesInventario.some(lote => (
      lote.novo || this.valorNumero(lote.quantidade_contada) !== this.valorNumero(lote.saldo_sistema)
    ));
  }

  get inventarioSemDiferenca(): boolean {
    return !this.inventarioPossuiDiferenca;
  }

  get loteSelecionado(): LoteSaida | undefined {
    return this.lotesPerda.find(lote => lote.id === this.loteId);
  }

  trocarOperacao(operacao: Operacao): void {
    this.operacao = operacao;
    this.erro = '';
    this.sucesso = '';
    this.loteId = undefined;
    this.lotesPerda = [];
    this.carregandoLotes = false;
    this.lotesInventario = [];
    this.lotesCargaInicial = [];
    this.carregandoLotesInventario = false;

    if (!this.itensDaOperacao.some(item => item.item_generico_id === this.itemGenericoId)) {
      this.itemGenericoId = undefined;
    }

    if (this.operacao === 'CARGA_INICIAL') {
      this.iniciarCargaInicial();
    } else if (this.operacao === 'INVENTARIO' && this.itemGenericoId) {
      this.carregarLotesParaInventario();
    } else if (this.operacao === 'SAIDA' && this.tipoSaida === 'PERDA' && this.itemGenericoId) {
      this.carregarLotesParaPerda();
    }
  }

  trocarGenero(itemGenericoId?: number): void {
    this.itemGenericoId = itemGenericoId;
    this.loteId = undefined;
    this.lotesInventario = [];
    this.lotesCargaInicial = [];

    if (this.operacao === 'SAIDA' && this.tipoSaida === 'PERDA') {
      this.carregarLotesParaPerda();
    } else {
      this.lotesPerda = [];
      this.carregandoLotes = false;
    }

    if (this.operacao === 'INVENTARIO') {
      this.carregarLotesParaInventario();
    } else if (this.operacao === 'CARGA_INICIAL') {
      this.iniciarCargaInicial();
    }
  }

  trocarTipoSaida(tipoSaida: string): void {
    this.tipoSaida = tipoSaida;
    this.loteId = undefined;
    if (this.tipoSaida === 'PERDA') {
      this.carregarLotesParaPerda();
    } else {
      this.lotesPerda = [];
      this.carregandoLotes = false;
    }
  }

  adicionarLoteCargaInicial(): void {
    this.lotesCargaInicial.push(this.novoLoteCargaInicial());
  }

  removerLoteCargaInicial(indice: number): void {
    if (this.lotesCargaInicial.length > 1) {
      this.lotesCargaInicial.splice(indice, 1);
    }
  }

  adicionarLoteInventario(): void {
    this.lotesInventario.push(this.novoLoteInventario());
  }

  removerLoteInventario(indice: number): void {
    if (this.lotesInventario[indice]?.novo) {
      this.lotesInventario.splice(indice, 1);
    }
  }

  salvar(): void {
    if (this.operacao === 'SAIDA') {
      if (!this.itemGenericoId || this.quantidade === undefined || this.quantidade === null || !this.justificativa.trim()) {
        this.erro = 'Preencha gênero, quantidade e justificativa.';
        return;
      }
      if (this.tipoSaida === 'PERDA' && !this.loteId) {
        this.erro = 'Selecione o lote que está sendo baixado por perda ou vencimento.';
        return;
      }
    } else {
      if (!this.itemGenericoId || !this.justificativa.trim()) {
        this.erro = 'Preencha gênero e justificativa.';
        return;
      }
      if (this.operacao === 'CARGA_INICIAL' && !this.validarLotesCargaInicial()) {
        return;
      }
      if (this.operacao === 'INVENTARIO' && !this.validarLotesInventario()) {
        return;
      }
    }

    this.processando = true;
    this.erro = '';
    this.sucesso = '';
    const base = {
      item_generico_id: this.itemGenericoId!,
      justificativa: this.justificativa,
      data_hora: new Date(this.dataHora).toISOString(),
    };
    const requisicao: Observable<unknown> = this.operacao === 'SAIDA'
      ? this.estoqueService.registrarSaida({
        ...base,
        quantidade: this.quantidade,
        tipo_saida: this.tipoSaida,
        ...(this.tipoSaida === 'PERDA' ? { lote_id: this.loteId } : {}),
      })
      : this.operacao === 'CARGA_INICIAL'
        ? this.estoqueService.registrarCargaInicial({
          ...base,
          lotes: this.lotesCargaInicial.map(lote => ({
            numero_lote: lote.numero_lote.trim(),
            data_validade: lote.data_validade,
            quantidade: Number(lote.quantidade),
          })),
        })
        : this.estoqueService.registrarAjuste({
          ...base,
          lotes: this.lotesInventario.map(lote => (
            lote.novo
              ? {
                numero_lote: lote.numero_lote.trim(),
                data_validade: lote.data_validade,
                quantidade_contada: Number(lote.quantidade_contada),
              }
              : {
                lote_id: lote.lote_id,
                quantidade_contada: Number(lote.quantidade_contada),
              }
          )),
        });

    requisicao.subscribe({
      next: () => {
        this.sucesso = 'Movimentação registrada com sucesso.';
        this.processando = false;
        this.quantidade = undefined;
        this.justificativa = '';
        this.loteId = undefined;
        if (this.operacao === 'CARGA_INICIAL') {
          this.lotesCargaInicial = [];
        }
        if (this.operacao === 'INVENTARIO') {
          this.lotesInventario = [];
        }
        this.carregarItens();
        if (this.operacao === 'SAIDA' && this.tipoSaida === 'PERDA') {
          this.carregarLotesParaPerda();
        }
      },
      error: erro => {
        this.erro = this.mensagemErro(erro.error);
        this.processando = false;
      },
    });
  }

  formatarDataValidade(data: string | null): string {
    if (!data) {
      return 'validade não informada';
    }
    const [ano, mes, dia] = data.split('-');
    return ano && mes && dia ? `validade ${dia}/${mes}/${ano}` : data;
  }

  private carregarItens(): void {
    this.estoqueService.listar('', 1, 100).subscribe(resposta => {
      this.itens = resposta.results;
      if (this.operacao === 'CARGA_INICIAL' && !this.itensSemCargaInicial.length) {
        this.trocarOperacao('SAIDA');
        return;
      }
      if (!this.itensDaOperacao.some(item => item.item_generico_id === this.itemGenericoId)) {
        this.itemGenericoId = undefined;
        this.lotesInventario = [];
        return;
      }
      if (this.operacao === 'INVENTARIO' && this.itemGenericoId) {
        this.carregarLotesParaInventario();
      }
    });
  }

  private iniciarCargaInicial(): void {
    this.lotesCargaInicial = [this.novoLoteCargaInicial()];
  }

  private novoLoteCargaInicial(): LoteCargaInicialForm {
    return {
      numero_lote: '',
      data_validade: '',
      quantidade: null,
    };
  }

  private novoLoteInventario(): LoteInventarioForm {
    return {
      numero_lote: '',
      data_validade: '',
      saldo_sistema: 0,
      quantidade_contada: null,
      legado: false,
      vencido: false,
      novo: true,
    };
  }

  private carregarLotesParaPerda(): void {
    if (!this.itemGenericoId) {
      this.lotesPerda = [];
      this.carregandoLotes = false;
      return;
    }
    this.carregandoLotes = true;
    this.estoqueService.listarLotesParaPerda(this.itemGenericoId).subscribe({
      next: lotes => {
        this.lotesPerda = lotes;
        this.carregandoLotes = false;
      },
      error: () => {
        this.lotesPerda = [];
        this.carregandoLotes = false;
        this.erro = 'Não foi possível carregar os lotes para perda.';
      },
    });
  }

  private carregarLotesParaInventario(): void {
    if (!this.itemGenericoId) {
      this.lotesInventario = [];
      this.carregandoLotesInventario = false;
      return;
    }
    const itemGenericoId = this.itemGenericoId;
    this.carregandoLotesInventario = true;
    this.estoqueService.listarLotesParaInventario(itemGenericoId).subscribe({
      next: lotes => {
        if (this.itemGenericoId !== itemGenericoId || this.operacao !== 'INVENTARIO') {
          return;
        }
        this.lotesInventario = lotes.map(lote => this.loteInventarioForm(lote));
        this.carregandoLotesInventario = false;
      },
      error: () => {
        if (this.itemGenericoId !== itemGenericoId || this.operacao !== 'INVENTARIO') {
          return;
        }
        this.lotesInventario = [];
        this.carregandoLotesInventario = false;
        this.erro = 'Não foi possível carregar os lotes para inventário.';
      },
    });
  }

  private loteInventarioForm(lote: LoteInventario): LoteInventarioForm {
    return {
      lote_id: lote.id,
      numero_lote: lote.numero_lote,
      data_validade: lote.data_validade,
      saldo_sistema: Number(lote.saldo_atual),
      quantidade_contada: Number(lote.saldo_atual),
      legado: lote.legado,
      vencido: lote.vencido,
      novo: false,
    };
  }

  private validarLotesCargaInicial(): boolean {
    if (!this.lotesCargaInicial.length) {
      this.erro = 'Informe ao menos um lote para a carga inicial.';
      return false;
    }

    const numeros = new Set<string>();
    for (const lote of this.lotesCargaInicial) {
      const numero = lote.numero_lote.trim();
      if (!numero || !lote.data_validade || !this.quantidadePositiva(lote.quantidade)) {
        this.erro = 'Preencha número, validade e quantidade válida para todos os lotes da carga inicial.';
        return false;
      }
      if (numero.toLocaleLowerCase() === 'legado') {
        this.erro = 'O identificador LEGADO é reservado e não pode ser utilizado em novas cargas iniciais.';
        return false;
      }
      const chave = numero.toLocaleLowerCase();
      if (numeros.has(chave)) {
        this.erro = 'O mesmo lote foi informado mais de uma vez para este item.';
        return false;
      }
      numeros.add(chave);
    }
    return true;
  }

  private validarLotesInventario(): boolean {
    if (this.carregandoLotesInventario) {
      this.erro = 'Aguarde o carregamento dos lotes do inventário.';
      return false;
    }

    const existentes = new Set(
      this.lotesInventario
        .filter(lote => !lote.novo)
        .map(lote => lote.numero_lote.trim().toLocaleLowerCase()),
    );
    const novos = new Set<string>();

    for (const lote of this.lotesInventario) {
      if (!lote.novo) {
        if (!this.quantidadeNaoNegativa(lote.quantidade_contada)) {
          this.erro = 'Informe uma quantidade contada válida para todos os lotes.';
          return false;
        }
        continue;
      }

      const numero = lote.numero_lote.trim();
      if (!numero || !lote.data_validade || !this.quantidadePositiva(lote.quantidade_contada)) {
        this.erro = 'Preencha número, validade e quantidade maior que zero para cada lote encontrado.';
        return false;
      }
      if (numero.toLocaleLowerCase() === 'legado') {
        this.erro = 'O identificador LEGADO é reservado e não pode ser utilizado como novo lote.';
        return false;
      }
      const chave = numero.toLocaleLowerCase();
      if (novos.has(chave) || existentes.has(chave)) {
        this.erro = 'O mesmo lote foi informado mais de uma vez para este item.';
        return false;
      }
      novos.add(chave);
    }

    if (this.inventarioSemDiferenca) {
      this.erro = 'A contagem confere com os saldos dos lotes; não há diferença a ajustar.';
      return false;
    }
    return true;
  }

  private quantidadePositiva(valor: number | null): boolean {
    return Number.isFinite(Number(valor)) && Number(valor) > 0;
  }

  private quantidadeNaoNegativa(valor: number | null): boolean {
    return Number.isFinite(Number(valor)) && Number(valor) >= 0;
  }

  private valorNumero(valor: number | null | undefined): number {
    const numero = Number(valor);
    return Number.isFinite(numero) ? numero : 0;
  }

  private mensagemErro(erro: any): string {
    if (!erro) return 'Não foi possível registrar a movimentação.';
    const valor = Object.values(erro)[0];
    return Array.isArray(valor) ? String(valor[0]) : String(valor);
  }

  private agoraLocalParaInput(): string {
    const agora = new Date();
    const ano = agora.getFullYear();
    const mes = String(agora.getMonth() + 1).padStart(2, '0');
    const dia = String(agora.getDate()).padStart(2, '0');
    const hora = String(agora.getHours()).padStart(2, '0');
    const minuto = String(agora.getMinutes()).padStart(2, '0');
    return `${ano}-${mes}-${dia}T${hora}:${minuto}`;
  }
}
