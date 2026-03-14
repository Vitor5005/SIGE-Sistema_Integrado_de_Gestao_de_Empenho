import { Injectable } from '@angular/core';
import { OrdemEntrega } from '../model/ordem_entrega';
import { OrdemEntregaInsert } from '../model/ordem_entrega_insert';
import { ICrudService } from './i-crud-service';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment.development';
import { HttpClient } from '@angular/common/http';
import { ItemOrdem } from '../model/itemOrdem';

@Injectable({
  providedIn: 'root',
})
export class OrdemEntregaService implements ICrudService<OrdemEntrega> {

  constructor(
    private http: HttpClient
  ) {}

  apiUrl = environment.API_URL + '/entregas/';
  
  get(termobusca?: string): Observable<OrdemEntrega[]> {
    let url = this.apiUrl
    if (termobusca) {
      url += `?search=${termobusca}`;
    }
    return this.http.get<OrdemEntrega[]>(url);
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
    return this.http.get<ItemOrdem[]>(url);
  }

  enviarEmail(id: number, arquivo: FormData): Observable<void> {
    let url = this.apiUrl + id + '/enviar-pedido/';
    return this.http.post<void>(url, arquivo);
  }
}
