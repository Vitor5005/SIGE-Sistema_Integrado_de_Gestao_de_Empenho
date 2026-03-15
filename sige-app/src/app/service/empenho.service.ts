import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { Empenho } from '../model/empenho';
import { map, Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';
import { EmpenhoInsert } from '../model/empenho_insert';
import { ItemEmpenho } from '../model/itemEmpenho';
import { OperacaoItem } from '../model/operacao_item';
import { normalizePaginatedResponse, PaginatedResponse } from '../model/pagination';

@Injectable({
  providedIn: 'root',
})
export class EmpenhoService implements ICrudService<Empenho> {

  constructor(
    private http: HttpClient
  ) { }
  apiUrl = environment.API_URL + '/empenhos/';

  get(termobusca?: string, page: number = 1, pageSize: number = 10, filtros: any = {}): Observable<PaginatedResponse<Empenho>> {
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

    return this.http.get<PaginatedResponse<Empenho> | Empenho[]>(url).pipe(
      map((response) => normalizePaginatedResponse<Empenho>(response))
    );
  }

  getById(id: number): Observable<Empenho> {
    let url = this.apiUrl + id + '/';
    return this.http.get<Empenho>(url);
  }

  save(item: EmpenhoInsert): Observable<EmpenhoInsert> {
    let url = this.apiUrl;
    if (item.id) {
      url += item.id + '/'
      return this.http.put<EmpenhoInsert>(url, item);
    }
    else {
      return this.http.post<EmpenhoInsert>(url, item);
    }
  }

  patch(id: number, object: any): Observable<any> {
    let url = this.apiUrl + id + '/';
    return this.http.patch(url, object);
  }

  itensDoEmpenho(id: number): Observable<any> {
    let url = this.apiUrl + `itensDoEmpenho/?empenho_id=` + id;
    return this.http.get<PaginatedResponse<ItemEmpenho> | ItemEmpenho[]>(url).pipe(
      map((response) => normalizePaginatedResponse<ItemEmpenho>(response).results)
    );
  }

  operacaoDoEmpenho(id: number): Observable<any> {
    let url = this.apiUrl + `operacaoDoEmpenho/?empenho_id=` + id;
    return this.http.get<PaginatedResponse<OperacaoItem> | OperacaoItem[]>(url).pipe(
      map((response) => normalizePaginatedResponse<OperacaoItem>(response).results)
    );
  }

  delete(id: number): Observable<void> {
    let url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);
  }
}