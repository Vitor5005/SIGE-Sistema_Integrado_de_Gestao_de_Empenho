import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { ItemGenerico } from '../model/item_generico';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class ItemGenericoService implements ICrudService<ItemGenerico> {

  constructor(
    private http: HttpClient
  ) { }

  apiUrl = environment.API_URL + '/itemgenericos/';

  get(termobusca?: string): Observable<ItemGenerico[]> {
    let url = this.apiUrl
    if (termobusca) {
      url += `?search=${termobusca}`;
    }
    return this.http.get<ItemGenerico[]>(url);
  }

  getById(id: number): Observable<ItemGenerico> {
    let url = this.apiUrl + id + '/';
    return this.http.get<ItemGenerico>(url);
  }

  save(item: any): Observable<any> {
    let url = this.apiUrl;
    if (item.id) {
      url += item.id + '/'
      return this.http.put<ItemGenerico>(url, item);
    }
    else {
      return this.http.post<ItemGenerico>(url, item);
    }
  }

  patch(id: number, object: any): Observable<any> {
    throw new Error('Method not implemented.');
  }

  delete(id: number): Observable<void> {
    let url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);
  }

}
