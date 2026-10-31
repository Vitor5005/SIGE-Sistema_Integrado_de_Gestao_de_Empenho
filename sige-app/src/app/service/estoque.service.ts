import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { map, Observable } from 'rxjs';

import { environment } from '../environments/environment';
import {
  AlertasValidade,
  EstoqueConsolidado,
  EstoqueItem,
  ItemRecebimento,
  LoteInventario,
  LoteSaida,
  LoteValidade,
  MovimentacaoEstoque,
  MovimentacaoEstoqueExtrato,
  RastreabilidadeLote,
  ResumoValidades,
} from '../model/estoque';
import { normalizePaginatedResponse, PaginatedResponse } from '../model/pagination';

@Injectable({ providedIn: 'root' })
export class EstoqueService {
  private readonly apiUrl = environment.API_URL + '/estoques/';
  private readonly movimentosUrl = environment.API_URL + '/movimentacoes-estoque/';
  private readonly lotesValidadeUrl = environment.API_URL + '/lotes-estoque/';

  constructor(private http: HttpClient) {}

  listar(search = '', page = 1, pageSize = 10, categoria = ''): Observable<PaginatedResponse<EstoqueItem>> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (search) params = params.set('search', search);
    if (categoria) params = params.set('item_generico__categoria', categoria);
    return this.http.get<PaginatedResponse<EstoqueItem> | EstoqueItem[]>(this.apiUrl, { params })
      .pipe(map(normalizePaginatedResponse));
  }

  consolidado(): Observable<EstoqueConsolidado[]> {
    return this.http.get<EstoqueConsolidado[]>(this.apiUrl + 'consolidado/');
  }

  extrato(
    generoId?: number,
    dataInicio?: string,
    dataFim?: string,
    loteId?: number,
  ): Observable<PaginatedResponse<MovimentacaoEstoqueExtrato>> {
    let params = new HttpParams().set('page_size', 100);
    if (generoId) params = params.set('genero_id', generoId);
    if (dataInicio) params = params.set('data_inicio', dataInicio);
    if (dataFim) params = params.set('data_fim', dataFim);
    if (loteId) params = params.set('lote_id', loteId);
    return this.http.get<PaginatedResponse<MovimentacaoEstoqueExtrato> | MovimentacaoEstoqueExtrato[]>(this.movimentosUrl, { params })
      .pipe(map(normalizePaginatedResponse));
  }

  rastreabilidadeLote(loteId: number): Observable<RastreabilidadeLote> {
    const params = new HttpParams().set('lote_id', loteId);
    return this.http.get<RastreabilidadeLote>(this.movimentosUrl + 'rastreabilidade-lote/', { params });
  }

  receber(ordemId: number, dataEntrada: string, itens: ItemRecebimento[]): Observable<unknown> {
    return this.http.post(this.apiUrl + 'recebimentos/', {
      ordem_id: ordemId,
      data_entrada: dataEntrada,
      itens,
    });
  }

  registrarSaida(payload: object): Observable<MovimentacaoEstoque> {
    return this.http.post<MovimentacaoEstoque>(this.apiUrl + 'saidas/', payload);
  }

  listarLotesParaPerda(itemGenericoId: number): Observable<LoteSaida[]> {
    const params = new HttpParams().set('item_generico_id', itemGenericoId);
    return this.http.get<LoteSaida[]>(this.apiUrl + 'lotes-para-perda/', { params });
  }

  listarLotesParaInventario(itemGenericoId: number): Observable<LoteInventario[]> {
    const params = new HttpParams().set('item_generico_id', itemGenericoId);
    return this.http.get<LoteInventario[]>(this.apiUrl + 'lotes-para-inventario/', { params });
  }

  listarLotesValidade(
    search = '',
    page = 1,
    pageSize = 10,
    filtros: Record<string, any> = {},
  ): Observable<PaginatedResponse<LoteValidade>> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (search) params = params.set('search', search);

    Object.entries(filtros).forEach(([campo, valor]) => {
      if (valor !== null && valor !== undefined && valor !== '') {
        params = params.set(campo, String(valor));
      }
    });

    return this.http.get<PaginatedResponse<LoteValidade> | LoteValidade[]>(this.lotesValidadeUrl, { params })
      .pipe(map(normalizePaginatedResponse));
  }

  resumoValidades(): Observable<ResumoValidades> {
    return this.http.get<ResumoValidades>(this.lotesValidadeUrl + 'resumo/');
  }

  alertasValidade(): Observable<AlertasValidade> {
    return this.http.get<AlertasValidade>(this.lotesValidadeUrl + 'alertas-validade/');
  }

  registrarCargaInicial(payload: object): Observable<MovimentacaoEstoque> {
    return this.http.post<MovimentacaoEstoque>(this.apiUrl + 'cargas-iniciais/', payload);
  }

  registrarAjuste(payload: object): Observable<MovimentacaoEstoque[]> {
    return this.http.post<MovimentacaoEstoque[]>(this.apiUrl + 'ajustes/', payload);
  }

  estornar(payload: object): Observable<MovimentacaoEstoque> {
    return this.http.post<MovimentacaoEstoque>(this.apiUrl + 'estornos/', payload);
  }
}

