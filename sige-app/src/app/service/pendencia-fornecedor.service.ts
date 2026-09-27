import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { map, Observable } from 'rxjs';

import { environment } from '../environments/environment.development';
import { normalizePaginatedResponse, PaginatedResponse } from '../model/pagination';
import { PendenciaFornecedor, StatusPendencia } from '../model/pendencia_fornecedor';

@Injectable({ providedIn: 'root' })
export class PendenciaFornecedorService {
  private readonly apiUrl = environment.API_URL + '/pendencias-fornecedor/';

  constructor(private http: HttpClient) {}

  listar(status?: StatusPendencia, page = 1, pageSize = 10): Observable<PaginatedResponse<PendenciaFornecedor>> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (status) params = params.set('status', status);
    return this.http.get<PaginatedResponse<PendenciaFornecedor> | PendenciaFornecedor[]>(this.apiUrl, { params })
      .pipe(map(normalizePaginatedResponse));
  }

  marcarCiente(id: number): Observable<PendenciaFornecedor> {
    return this.http.post<PendenciaFornecedor>(`${this.apiUrl}${id}/ciente/`, {});
  }
}
