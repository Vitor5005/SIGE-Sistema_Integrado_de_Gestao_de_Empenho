import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { Fornecedor } from '../model/fornecedor';
import { map, Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';
import { FornecedorInsert } from '../model/fornecedor_insert';
import { normalizePaginatedResponse, PaginatedResponse } from '../model/pagination';

@Injectable({
  providedIn: 'root',
})
export class FornecedorService implements ICrudService<Fornecedor> {

  constructor(
    private http: HttpClient
  ) { }

  apiUrl = environment.API_URL + '/fornecedores/';

  get(termobusca?: string, page: number = 1, pageSize: number = 10, filtros: any = {}): Observable<PaginatedResponse<Fornecedor>> {
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
    return this.http.get<PaginatedResponse<Fornecedor> | Fornecedor[]>(url).pipe(
      map((response) => normalizePaginatedResponse<Fornecedor>(response))
    );

  }

  getById(id: number): Observable<Fornecedor> {

    const url = this.apiUrl + id + '/';
    return this.http.get<Fornecedor>(url);

  }

  save(item: FornecedorInsert): Observable<FornecedorInsert> {
    let url = this.apiUrl;
    if (item.id) {
      console.log(url);
      url += item.id + "/"
      return this.http.put<FornecedorInsert>(url, item);
    }
    else {
      return this.http.post<FornecedorInsert>(url, item);
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
