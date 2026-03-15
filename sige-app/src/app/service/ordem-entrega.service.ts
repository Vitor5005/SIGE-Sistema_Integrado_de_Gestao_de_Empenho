import { Injectable } from '@angular/core';
import { OrdemEntrega } from '../model/ordem_entrega';
import { OrdemEntregaInsert } from '../model/ordem_entrega_insert';
import { ICrudService } from './i-crud-service';
import { map, Observable } from 'rxjs';
import { environment } from '../environments/environment.development';
import { HttpClient } from '@angular/common/http';
import { ItemOrdem } from '../model/itemOrdem';
import { normalizePaginatedResponse, PaginatedResponse } from '../model/pagination';

@Injectable({
  providedIn: 'root',
})
export class OrdemEntregaService implements ICrudService<OrdemEntrega> {

  constructor(
    private http: HttpClient
  ) {}

  apiUrl = environment.API_URL + '/entregas/';

  get(termobusca?: string, page: number = 1, pageSize: number = 10, filtros: any = {}): Observable<PaginatedResponse<OrdemEntrega>> {
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
    return this.http.get<PaginatedResponse<OrdemEntrega> | OrdemEntrega[]>(url).pipe(
      map((response) => normalizePaginatedResponse<OrdemEntrega>(response))
    );
  }

  getComFiltros(filtros: any = {}, page: number = 1, pageSize: number = 10): Observable<PaginatedResponse<OrdemEntrega>> {
    const filtrosParaEnvio = { ...filtros };
    const search = filtrosParaEnvio.search || '';

    delete filtrosParaEnvio.search;

    return this.get(search, page, pageSize, filtrosParaEnvio);
  }

  getById(id: number): Observable<OrdemEntrega> {
    let url = this.apiUrl + id + '/';
    return this.http.get<OrdemEntrega>(url);
  }


  save(item: OrdemEntregaInsert): Observable<OrdemEntregaInsert> {
    let url = this.apiUrl;
    if (item.id) {
      url += item.id + '/'
      return this.http.put<OrdemEntregaInsert>(url, item);
    }
    else {
      return this.http.post<OrdemEntregaInsert>(url, item);
    }
  }

  delete(id: number): Observable<void> {
    let url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);
  }

  patch(id: number, object: any): Observable<any> {
    let url = this.apiUrl + id + '/';
    return this.http.patch(url, object);
  }

  getPedidos(id: number): Observable<ItemOrdem[]> {
    let url = this.apiUrl + `pedidos/?ordem_id=` + id;
    return this.http.get<PaginatedResponse<ItemOrdem> | ItemOrdem[]>(url).pipe(
      map((response) => normalizePaginatedResponse<ItemOrdem>(response).results)
    );
  }

  enviarEmail(id: number, arquivo: FormData): Observable<void> {
    let url = this.apiUrl + id + '/enviar-pedido/';
    return this.http.post<void>(url, arquivo);
  }
}
