import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { Fornecedor } from '../model/fornecedor';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class FornecedorService implements ICrudService<Fornecedor> {

  constructor(
    private http: HttpClient
  ) { }

  apiUrl = environment.API_URL + '/fornecedores/';

  get(termobusca?: string): Observable<Fornecedor[]> {

    let url = this.apiUrl;
    if (termobusca) {
      url += '?search=' + termobusca;
    }
    return this.http.get<Fornecedor[]>(url);

  }

  getById(id: number): Observable<Fornecedor> {

    const url = this.apiUrl + id + '/';
    return this.http.get<Fornecedor>(url);

  }

  save(item: Fornecedor): Observable<Fornecedor> {
    let url = environment.API_URL
    if (item.id) {
      url += item.id + "/"
      return this.http.put<Fornecedor>(url, item);
    }
    else {
      return this.http.post<Fornecedor>(url, item);
    }

  }

  delete(id: number): Observable<void> {

    const url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);

  }



}
