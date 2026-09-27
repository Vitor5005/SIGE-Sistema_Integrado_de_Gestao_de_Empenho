import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { map, Observable } from 'rxjs';

import { environment } from '../environments/environment';
import { normalizePaginatedResponse, PaginatedResponse } from '../model/pagination';
import { SolicitacaoReforco, StatusSolicitacaoReforco } from '../model/solicitacao_reforco';

@Injectable({ providedIn: 'root' })
export class SolicitacaoReforcoService {
  private readonly apiUrl = environment.API_URL + '/solicitacoes-reforco/';

  constructor(private http: HttpClient) {}

  listar(
    filtros: { status?: StatusSolicitacaoReforco; empenhoId?: number; naoVistas?: boolean } = {},
    page = 1,
    pageSize = 20,
  ):
    Observable<PaginatedResponse<SolicitacaoReforco>> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (filtros.status) params = params.set('status', filtros.status);
    if (filtros.empenhoId) params = params.set('item_empenho__empenho__id', filtros.empenhoId);
    if (filtros.naoVistas) params = params.set('vista_pelo_solicitante', 'false');
    return this.http.get<PaginatedResponse<SolicitacaoReforco> | SolicitacaoReforco[]>(this.apiUrl, { params })
      .pipe(map(normalizePaginatedResponse));
  }

  saldoDisponivel(itemEmpenhoId: number): Observable<number> {
    const params = new HttpParams().set('item_empenho', itemEmpenhoId);
    return this.http.get<{ saldo_disponivel: string }>(this.apiUrl + 'saldo/', { params })
      .pipe(map(resposta => Number(resposta.saldo_disponivel)));
  }

  solicitar(itemEmpenhoId: number, quantidade: number, justificativa: string): Observable<SolicitacaoReforco> {
    return this.http.post<SolicitacaoReforco>(this.apiUrl, {
      item_empenho: itemEmpenhoId,
      quantidade,
      justificativa,
    });
  }

  atender(id: number): Observable<SolicitacaoReforco> {
    return this.http.post<SolicitacaoReforco>(`${this.apiUrl}${id}/atender/`, {});
  }

  marcarVista(id: number): Observable<SolicitacaoReforco> {
    return this.http.post<SolicitacaoReforco>(`${this.apiUrl}${id}/marcar-vista/`, {});
  }

  recusar(id: number, resposta: string): Observable<SolicitacaoReforco> {
    return this.http.post<SolicitacaoReforco>(`${this.apiUrl}${id}/recusar/`, { resposta });
  }
}
