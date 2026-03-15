import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { Usuario } from '../model/usuario';
import { map, Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';
import { normalizePaginatedResponse, PaginatedResponse } from '../model/pagination';

@Injectable({
  providedIn: 'root',
})
export class UsuarioService implements ICrudService<Usuario> {
  
  constructor(
    private http: HttpClient
  ) {}
  
  apiUrl = environment.API_URL + '/usuarios/';
  
  get(termobusca?: string, page: number = 1, pageSize: number = 10, filtros: any = {}): Observable<PaginatedResponse<Usuario>> {
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

    return this.http.get<PaginatedResponse<Usuario> | Usuario[]>(url).pipe(
      map((response) => normalizePaginatedResponse<Usuario>(response))
    );
  }

  getById(id: number): Observable<Usuario> {
    let url = this.apiUrl + id + '/';
    return this.http.get<Usuario>(url);
  }
  
  save(item: any): Observable<any> {
    if(item.id) {
      let url = this.apiUrl + item.id + '/';
      return this.http.put(url, item);
    }
    return this.http.post(this.apiUrl, item);
  }

  delete(id: number): Observable<void> {
    let url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);
  }
  
  patch(id: number, object: any): Observable<any> {
    let url = this.apiUrl + id + '/';
    return this.http.patch(url, object);
  }
  
}
