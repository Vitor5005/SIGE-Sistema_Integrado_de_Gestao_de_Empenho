import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { Licitacao } from '../model/licitacao';
import { map, Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';
import { normalizePaginatedResponse, PaginatedResponse, PaginationParams } from '../model/pagination';

@Injectable({
  providedIn: 'root',
})
export class LicitacaoService implements ICrudService<Licitacao> {

  constructor(
    private http: HttpClient
  ) { }

  apiUrl = environment.API_URL + '/licitacoes/';

  get(termobusca?: string, page: number = 1, pageSize: number = 10, filtros: any = {}): Observable<PaginatedResponse<Licitacao>> {
    const params = new URLSearchParams();
    params.set('page', String(page));
    params.set('page_size', String(pageSize));

    if (termobusca) {
      params.set('search', termobusca);
    }

    Object.entries(filtros || {}).forEach(([chave, valor]) => {
      if (valor !== null && valor !== undefined && valor !== '') {
        params.set(chave, String(valor));
      }
    });

    const url = `${this.apiUrl}?${params.toString()}`;

    return this.http.get<PaginatedResponse<Licitacao> | Licitacao[]>(url).pipe(
      map((response) => normalizePaginatedResponse<Licitacao>(response))
    );
  }

  getComFiltros(filtros: PaginationParams = {}): Observable<PaginatedResponse<Licitacao>> {
    const page = filtros.page || 1;
    const pageSize = filtros.page_size || 10;
    const search = filtros.search;

    const filtrosRestantes = { ...filtros };
    delete filtrosRestantes.page;
    delete filtrosRestantes.page_size;
    delete filtrosRestantes.search;

    return this.get(search, page, pageSize, filtrosRestantes);
  }

  getById(id: number): Observable<Licitacao> {
    const url = this.apiUrl + id + '/';
    return this.http.get<Licitacao>(url);
  }

  save(item: Licitacao): Observable<Licitacao> {
    let url = this.apiUrl;
    if (item.id) {
      url += item.id + '/';
      return this.http.put<Licitacao>(url, item);
    }
    else {
      return this.http.post<Licitacao>(url, item);
    }
  }

  patch(id: number, object: any): Observable<any> {
    throw new Error('Method not implemented.');
  }

  delete(id: number): Observable<void> {
    const url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);
  }

}
