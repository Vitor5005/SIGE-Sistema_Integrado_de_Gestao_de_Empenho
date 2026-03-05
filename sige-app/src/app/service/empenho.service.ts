import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { Empenho } from '../model/empenho';
import { map, Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';

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

  save(item: Empenho): Observable<Empenho> {
    let url = this.apiUrl;
    if (item.id) {
      url += item.id + '/'
      return this.http.put<Empenho>(url, item);
    }
    else {
      return this.http.post<Empenho>(url, item);
    }
  }

  delete(id: number): Observable<void> {
    let url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);
  }
}