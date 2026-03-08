import { Injectable } from '@angular/core';
import { ItemOrdem } from '../model/itemOrdem';
import { ICrudService } from './i-crud-service';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class ItemOrdemService implements ICrudService<ItemOrdem> {

  constructor(
    private http: HttpClient
  ){}

  apiUrl = environment.API_URL + '/itementregas/';
  
  get(termobusca?: string): Observable<ItemOrdem[]> {
    let url = this.apiUrl
    if (termobusca) {
      url += `?search=${termobusca}`;
    }
    return this.http.get<ItemOrdem[]>(url);
  }

  getById(id: number): Observable<ItemOrdem> {
    let url = this.apiUrl + id + '/';
    return this.http.get<ItemOrdem>(url);
  }

  save(item: any): Observable<any> {
    let url = this.apiUrl;
    if (item.id) {
      url += item.id + '/'
      return this.http.put(url, item);
    }
    else {
      return this.http.post(url, item);
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
  
  

}
