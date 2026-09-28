import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../environments/environment';
import { PainelNutricionista } from '../model/painel_nutricionista';

@Injectable({ providedIn: 'root' })
export class PainelNutricionistaService {
  private readonly apiUrl = environment.API_URL + '/painel-nutricionista/';

  constructor(private http: HttpClient) {}

  carregar(): Observable<PainelNutricionista> {
    return this.http.get<PainelNutricionista>(this.apiUrl);
  }
}
