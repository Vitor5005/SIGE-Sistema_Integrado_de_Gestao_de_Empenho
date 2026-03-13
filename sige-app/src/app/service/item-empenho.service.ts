import { Injectable } from '@angular/core';
import { ICrudService } from './i-crud-service';
import { ItemEmpenho } from '../model/itemEmpenho';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class ItemEmpenhoService implements ICrudService<ItemEmpenho> {

  constructor(
    private http: HttpClient
  ) { }

  apiUrl = environment.API_URL + '/itemempenho/';

  get(termobusca?: string): Observable<ItemEmpenho[]> {
    let url = this.apiUrl;
    if (termobusca) {
      url += `?search=${termobusca}`;
    }
    return this.http.get<ItemEmpenho[]>(url);
  }

  getById(id: number): Observable<ItemEmpenho> {
    let url = this.apiUrl + id + '/';
    return this.http.get<ItemEmpenho>(url);
  }

  save(item: any): Observable<any> {
    let url = this.apiUrl;
    if (item.id) {
      url += item.id + '/';
      return this.http.put(url, item);
    }
    return this.http.post(url, item);
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
