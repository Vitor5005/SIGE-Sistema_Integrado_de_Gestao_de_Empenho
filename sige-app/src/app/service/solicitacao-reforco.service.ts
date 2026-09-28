import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { map, Observable } from 'rxjs';

import { environment } from '../environments/environment';
import { normalizePaginatedResponse, PaginatedResponse } from '../model/pagination';
import {
  SolicitacaoReforco,
  SolicitacaoReforcoInsert,
  StatusSolicitacaoReforco,
} from '../model/solicitacao_reforco';

@Injectable({ providedIn: 'root' })
export class SolicitacaoReforcoService {
  private readonly apiUrl = environment.API_URL + '/solicitacoes-reforco/';

  constructor(private http: HttpClient) {}

  listar(
    status?: StatusSolicitacaoReforco,
    page = 1,
    pageSize = 10,
  ): Observable<PaginatedResponse<SolicitacaoReforco>> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (status) {
      params = params.set('status', status);
    }

    return this.http
      .get<PaginatedResponse<SolicitacaoReforco> | SolicitacaoReforco[]>(this.apiUrl, { params })
      .pipe(map(normalizePaginatedResponse));
  }

  solicitar(payload: SolicitacaoReforcoInsert): Observable<SolicitacaoReforco> {
    return this.http.post<SolicitacaoReforco>(this.apiUrl, payload);
  }

  marcarCiente(id: number): Observable<SolicitacaoReforco> {
    return this.http.post<SolicitacaoReforco>(`${this.apiUrl}${id}/ciente/`, {});
  }
}
