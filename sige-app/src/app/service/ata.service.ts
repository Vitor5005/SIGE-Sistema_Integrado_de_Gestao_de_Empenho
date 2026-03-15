import { Injectable } from '@angular/core';
import { Ata } from '../model/ata';
import { ICrudService } from './i-crud-service';
import { map, Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';
import { Empenho } from '../model/empenho';
import { ItemAta } from '../model/itemAta';
import { ItemEmpenho } from '../model/itemEmpenho';
import { AtaInsert } from '../model/ata_insert';
import { normalizePaginatedResponse, PaginatedResponse } from '../model/pagination';

@Injectable({
  providedIn: 'root',
})
export class AtaService implements ICrudService<Ata> {

  constructor(
    private http: HttpClient
  ) { }



  apiUrl = environment.API_URL + '/atas/';

  get(params?: any, page: number = 1, pageSize: number = 10): Observable<PaginatedResponse<Ata>> {
    const queryParams = { ...(params || {}) };
    queryParams.page = page;
    queryParams.page_size = pageSize;

    return this.http.get<PaginatedResponse<Ata> | Ata[]>(this.apiUrl, { params: queryParams }).pipe(
      map((response) => normalizePaginatedResponse<Ata>(response))
    );
  }

  getByLicicao(termobusca?: string, page: number = 1, pageSize: number = 10): Observable<PaginatedResponse<Ata>> {
    const params: any = {
      licitacao__id: termobusca || '',
      page,
      page_size: pageSize,
    };

    if (!termobusca) {
      delete params.licitacao__id;
    }

    return this.http.get<PaginatedResponse<Ata> | Ata[]>(this.apiUrl, { params }).pipe(
      map((response) => normalizePaginatedResponse<Ata>(response))
    );
  }

  getById(id: number): Observable<Ata> {
    const url = this.apiUrl + id + '/';
    return this.http.get<Ata>(url);
  }

  save(item: AtaInsert): Observable<AtaInsert> {
    let url = this.apiUrl;
    if (item.id) {
      url += item.id + '/';
      return this.http.put<AtaInsert>(url, item);
    }
    else {
      return this.http.post<AtaInsert>(url, item);
    }
  }

  patch(id: number, object: any): Observable<any> {
    const url = this.apiUrl + id + '/';
    return this.http.patch<Ata>(url, object);
  }

  delete(id: number): Observable<void> {
    const url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);
  }

  getEmpenho(ataId: number): Observable<Empenho> {
    const url = this.apiUrl + 'empenho/?ata_id=' + ataId;
    return this.http.get<Empenho>(url);
  }

  getItens(ataId: number): Observable<ItemEmpenho[]> {
    const url = this.apiUrl + 'itens_da_ata/?ata_id=' + ataId;
    return this.http.get<PaginatedResponse<ItemEmpenho> | ItemEmpenho[]>(url).pipe(
      map((response) => normalizePaginatedResponse<ItemEmpenho>(response).results)
    );
  }

}
