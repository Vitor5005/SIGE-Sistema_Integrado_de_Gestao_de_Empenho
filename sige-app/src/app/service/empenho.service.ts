import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { Empenho } from '../model/empenho';
import { map, Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';
import { EmpenhoInsert } from '../model/empenho_insert';
import { ItemEmpenho } from '../model/itemEmpenho';
import { OperacaoItem } from '../model/operacao_item';

@Injectable({
  providedIn: 'root',
})
export class EmpenhoService implements ICrudService<Empenho> {

  constructor(
    private http: HttpClient
  ) { }
  apiUrl = environment.API_URL + '/empenhos/';

  get(termobusca?: string): Observable<Empenho[]> {
    let url = this.apiUrl
    if (termobusca) {
      url += `?search=${termobusca}`;
    }
    return this.http.get<Empenho[]>(url);
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
    return this.http.get<ItemEmpenho[]>(url);
  }

  operacaoDoEmpenho(id: number): Observable<any> {
    let url = this.apiUrl + `operacaoDoEmpenho/?empenho_id=` + id;
    return this.http.get<OperacaoItem[]>(url);
  }

  delete(id: number): Observable<void> {
    let url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);
  }
}