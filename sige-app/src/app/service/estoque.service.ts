import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { map, Observable } from 'rxjs';

import { environment } from '../environments/environment.development';
import { EstoqueConsolidado, EstoqueItem, ItemRecebimento, MovimentacaoEstoque } from '../model/estoque';
import { normalizePaginatedResponse, PaginatedResponse } from '../model/pagination';

@Injectable({ providedIn: 'root' })
export class EstoqueService {
  private readonly apiUrl = environment.API_URL + '/estoques/';
  private readonly movimentosUrl = environment.API_URL + '/movimentacoes-estoque/';

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

  extrato(generoId?: number, dataInicio?: string, dataFim?: string): Observable<PaginatedResponse<MovimentacaoEstoque>> {
    let params = new HttpParams().set('page_size', 100);
    if (generoId) params = params.set('genero_id', generoId);
    if (dataInicio) params = params.set('data_inicio', dataInicio);
    if (dataFim) params = params.set('data_fim', dataFim);
    return this.http.get<PaginatedResponse<MovimentacaoEstoque> | MovimentacaoEstoque[]>(this.movimentosUrl, { params })
      .pipe(map(normalizePaginatedResponse));
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

  registrarCargaInicial(payload: object): Observable<MovimentacaoEstoque> {
    return this.http.post<MovimentacaoEstoque>(this.apiUrl + 'cargas-iniciais/', payload);
  }

  registrarAjuste(payload: object): Observable<MovimentacaoEstoque> {
    return this.http.post<MovimentacaoEstoque>(this.apiUrl + 'ajustes/', payload);
  }

  estornar(payload: object): Observable<MovimentacaoEstoque> {
    return this.http.post<MovimentacaoEstoque>(this.apiUrl + 'estornos/', payload);
  }
}

