import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { Licitacao } from '../model/licitacao';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class LicitacaoService implements ICrudService<Licitacao> {

  constructor(
    private http: HttpClient
  ) { }

  apiUrl = environment.API_URL + '/licitacoes/';

  get(termobusca?: string): Observable<Licitacao[]> {
    let url = this.apiUrl;
    if (termobusca) {
      url += '?search=' + termobusca;
    }
    return this.http.get<Licitacao[]>(url);
  }

  getById(id: number): Observable<Licitacao> {
    const url = this.apiUrl + id + '/';
    return this.http.get<Licitacao>(url);
  }

  save(item: Licitacao): Observable<Licitacao> {
    if (item.id) {
      return this.http.put<Licitacao>(this.apiUrl, item);
    }
    else {
      return this.http.post<Licitacao>(this.apiUrl, item);
    }
  }
  delete(id: number): Observable<void> {
    const url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);
  }

}
