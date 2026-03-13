import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';
import { OperacaoItem } from '../model/operacao_item';
import { OperacaoItemInsert } from '../model/operacao_item_insert';

@Injectable({
  providedIn: 'root',
})
export class OperacaoItemService implements ICrudService<OperacaoItem> {

  constructor(
    private http: HttpClient
  ) { }

  apiUrl = environment.API_URL + '/operacaoitens/';

  get(termobusca?: string): Observable<OperacaoItem[]> {
    let url = this.apiUrl;
    if (termobusca) {
      url += `?search=${termobusca}`;
    }
    return this.http.get<OperacaoItem[]>(url);
  }

  getById(id: number): Observable<OperacaoItem> {
    let url = this.apiUrl + id + '/';
    return this.http.get<OperacaoItem>(url);
  }

  save(item: OperacaoItemInsert): Observable<OperacaoItemInsert> {
    let url = this.apiUrl;
    if (item.id) {
      url += item.id + '/';
      return this.http.put<OperacaoItemInsert>(url, item);
    }
    return this.http.post<OperacaoItemInsert>(url, item);
  }

  patch(id: number, object: any): Observable<any> {
    throw new Error('Method not implemented.');
  }

  delete(id: number): Observable<void> {
    let url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);
  }

}
