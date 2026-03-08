import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { ItemAta } from '../model/itemAta';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';
import { ItemAtaInsert } from '../model/itemAta_insert';

@Injectable({
  providedIn: 'root',
})
export class ItemAtaService implements ICrudService<ItemAta> {

  constructor(
    private http: HttpClient
  ) { }

  apiUrl = environment.API_URL + '/itematas/';

  get(termobusca?: string): Observable<ItemAta[]> {
    let url = this.apiUrl
    if (termobusca) {
      url += `?search=${termobusca}`;
    }
    return this.http.get<ItemAta[]>(url);
  }

  getById(id: number): Observable<ItemAta> {
    let url = this.apiUrl + id + '/';
    return this.http.get<ItemAta>(url);
  }

  save(item: ItemAtaInsert): Observable<ItemAtaInsert> {
    let url = this.apiUrl;
    if (item.id) {
      url += item.id + '/';
      return this.http.put<ItemAtaInsert>(url, item);
    }
    else {
      return this.http.post<ItemAtaInsert>(url, item);
    }
  }

  patch(id: number, object: any): Observable<any> {
    let url = this.apiUrl + id + '/';
    return this.http.patch(url, object);
  }

  delete(id: number): Observable<void> {
    let url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);
  }


}
