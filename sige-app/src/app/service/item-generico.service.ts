import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { ItemGenerico } from '../model/item_generico';
import { map, Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';
import { normalizePaginatedResponse, PaginatedResponse } from '../model/pagination';

@Injectable({
  providedIn: 'root',
})
export class ItemGenericoService implements ICrudService<ItemGenerico> {

  constructor(
    private http: HttpClient
  ) { }

  apiUrl = environment.API_URL + '/itemgenericos/';

  get(termobusca?: string, page: number = 1, pageSize: number = 10, filtros: any = {}): Observable<PaginatedResponse<ItemGenerico>> {
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
    return this.http.get<PaginatedResponse<ItemGenerico> | ItemGenerico[]>(url).pipe(
      map((response) => normalizePaginatedResponse<ItemGenerico>(response))
    );
  }

  getById(id: number): Observable<ItemGenerico> {
    let url = this.apiUrl + id + '/';
    return this.http.get<ItemGenerico>(url);
  }

  save(item: any): Observable<any> {
    let url = this.apiUrl;
    if (item.id) {
      url += item.id + '/'
      return this.http.put<ItemGenerico>(url, item);
    }
    else {
      return this.http.post<ItemGenerico>(url, item);
    }
  }

  patch(id: number, object: any): Observable<any> {
    throw new Error('Method not implemented.');
  }

  delete(id: number): Observable<void> {
    let url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);
  }

  getComFiltros(params: any) {

    let httpParams: any = {};

    Object.entries(params).forEach(([key, value]) => {

      if (Array.isArray(value)) {
        httpParams[key] = value; // envia múltiplos
      } else {
        httpParams[key] = value;
      }

    });

    return this.http.get<ItemGenerico[]>(this.apiUrl, {
      params: httpParams
    });

  }
}
