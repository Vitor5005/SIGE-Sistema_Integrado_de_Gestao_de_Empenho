import { Injectable } from '@angular/core';
import { Ata } from '../model/ata';
import { ICrudService } from './i-crud-service';
import { map, Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';
import { Empenho } from '../model/empenho';
import { ItemAta } from '../model/itemAta';
import { ItemEmpenho } from '../model/itemEmpenho';

@Injectable({
  providedIn: 'root',
})
export class AtaService implements ICrudService<Ata> {

  constructor(
    private http: HttpClient
  ) { }

  apiUrl = environment.API_URL + '/atas/';

  get(termobusca?: string): Observable<Ata[]> {
    let url = this.apiUrl;
    if (termobusca) {
      url += '?search=' + termobusca;
    }
    return this.http.get<Ata[]>(url);
  }

  getById(id: number): Observable<Ata> {
    const url = this.apiUrl + id + '/';
    return this.http.get<Ata>(url);
  }

  save(item: Ata): Observable<Ata> {
    if (item.id) {
      return this.http.put<Ata>(this.apiUrl, item);
    }
    else {
      return this.http.post<Ata>(this.apiUrl, item);
    }
  }

  delete(id: number): Observable<void> {
    const url = this.apiUrl + id + '/';
    return this.http.delete<void>(url);
  }

  getEmpenho(ataId: number): Observable<Empenho> {
   const url = this.apiUrl + 'empenho/?ata_id=' + ataId;
   return this.http.get<Empenho>(url);
  }

  getItens(ataId: number): Observable<ItemEmpenho[]> {
    const url = this.apiUrl + 'itens_da_ata/?ata_id=' + ataId;
    return this.http.get<ItemEmpenho[]>(url);
  }

}
