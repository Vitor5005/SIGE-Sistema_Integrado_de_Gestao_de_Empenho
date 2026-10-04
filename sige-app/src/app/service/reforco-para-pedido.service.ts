import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { map, Observable } from 'rxjs';

import { environment } from '../environments/environment';
import { normalizePaginatedResponse, PaginatedResponse } from '../model/pagination';
import { ReforcoParaPedido } from '../model/reforco_para_pedido';

@Injectable({ providedIn: 'root' })
export class ReforcoParaPedidoService {
  private readonly apiUrl = environment.API_URL + '/reforcos-para-pedido/';

  constructor(private http: HttpClient) {}

  listar(page = 1, pageSize = 10): Observable<PaginatedResponse<ReforcoParaPedido>> {
    const params = new HttpParams().set('page', page).set('page_size', pageSize);
    return this.http.get<PaginatedResponse<ReforcoParaPedido> | ReforcoParaPedido[]>(this.apiUrl, { params })
      .pipe(map(normalizePaginatedResponse));
  }

  marcarCiente(id: number): Observable<ReforcoParaPedido> {
    return this.http.post<ReforcoParaPedido>(`${this.apiUrl}${id}/ciente/`, {});
  }
}
