import { Injectable } from '@angular/core';
import { Endereco } from '../model/endereco';
import { ICrudService } from './i-crud-service';
import { Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { environment } from '../environments/environment.development';

@Injectable({
  providedIn: 'root',
})
export class EnderecoService implements ICrudService<Endereco> {

    constructor(
      private http: HttpClient
    ){}

    apiUrl = environment.API_URL + '/enderecos/';

    get(): Observable<Endereco[]> {
      return this.http.get<Endereco[]>(this.apiUrl);
    }

    getById(id: number): Observable<Endereco> {
      const url = this.apiUrl + id + '/';
      return this.http.get<Endereco>(url);
    }

    save(item: Endereco): Observable<Endereco> {
      if (item.id) {
        return this.http.put<Endereco>(this.apiUrl, item);
      }
      else{
        return this.http.post<Endereco>(this.apiUrl, item);
      }
    }

    delete(id: number): Observable<void> {
      const url = this.apiUrl + id + '/';
      return this.http.delete<void>(url);
    }
    
}
