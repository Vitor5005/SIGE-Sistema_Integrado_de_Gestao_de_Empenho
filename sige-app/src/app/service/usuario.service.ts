import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { Usuario } from '../model/usuario';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class UsuarioService implements ICrudService<Usuario> {
  
  constructor(
    private http: HttpClient
  ) {}
  
  apiUrl = environment.API_URL + '/usuarios/';
  
  get(termobusca?: string): Observable<Usuario[]> {
    return this.http.get<Usuario[]>(this.apiUrl);
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
