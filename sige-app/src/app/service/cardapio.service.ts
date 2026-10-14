import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map, Observable } from 'rxjs';

import { environment } from '../environments/environment';
import {
  Cardapio,
  CardapioInsert,
  CardapioResumo,
  DisponibilidadeGenero,
  QuantidadeItemCardapio,
} from '../model/cardapio';
import { normalizePaginatedResponse, PaginatedResponse } from '../model/pagination';

@Injectable({ providedIn: 'root' })
export class CardapioService {
  private readonly apiUrl = environment.API_URL + '/cardapios/';

  constructor(private http: HttpClient) {}

  listar(filtros: { search?: string; status?: string; refeicao?: string } = {}, page = 1, pageSize = 10):
    Observable<PaginatedResponse<CardapioResumo>> {
    let params = new HttpParams().set('page', page).set('page_size', pageSize);
    if (filtros.search) params = params.set('search', filtros.search);
    if (filtros.refeicao) params = params.set('refeicao', filtros.refeicao);
    if (filtros.status) {
      params = filtros.status.includes(',')
        ? params.set('status__in', filtros.status)
        : params.set('status', filtros.status);
    }
    return this.http.get<PaginatedResponse<CardapioResumo> | CardapioResumo[]>(this.apiUrl, { params })
      .pipe(map(normalizePaginatedResponse));
  }

  obter(id: number): Observable<Cardapio> {
    return this.http.get<Cardapio>(`${this.apiUrl}${id}/`);
  }

  salvar(cardapio: CardapioInsert, id?: number): Observable<Cardapio> {
    return id
      ? this.http.put<Cardapio>(`${this.apiUrl}${id}/`, cardapio)
      : this.http.post<Cardapio>(this.apiUrl, cardapio);
  }

  excluir(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}${id}/`);
  }

  disponibilidade(cardapioId?: number): Observable<DisponibilidadeGenero[]> {
    let params = new HttpParams();
    if (cardapioId) params = params.set('cardapio', cardapioId);
    return this.http.get<DisponibilidadeGenero[]>(this.apiUrl + 'disponibilidade/', { params });
  }

  enviar(id: number): Observable<Cardapio> {
    return this.http.post<Cardapio>(`${this.apiUrl}${id}/enviar/`, {});
  }

  aprovar(id: number, itens: QuantidadeItemCardapio[]): Observable<Cardapio> {
    return this.http.post<Cardapio>(`${this.apiUrl}${id}/aprovar/`, { itens });
  }

  recusar(id: number, motivo: string): Observable<Cardapio> {
    return this.http.post<Cardapio>(`${this.apiUrl}${id}/recusar/`, { motivo });
  }

  informarConsumo(id: number, itens: QuantidadeItemCardapio[]): Observable<Cardapio> {
    return this.http.post<Cardapio>(`${this.apiUrl}${id}/informar-consumo/`, { itens });
  }

  devolverConsumo(id: number, motivo: string): Observable<Cardapio> {
    return this.http.post<Cardapio>(`${this.apiUrl}${id}/devolver-consumo/`, { motivo });
  }

  confirmarConsumo(id: number): Observable<Cardapio> {
    return this.http.post<Cardapio>(`${this.apiUrl}${id}/confirmar-consumo/`, {});
  }
}

/** Extrai a primeira mensagem legível de um erro da API. */
export function mensagemErroCardapio(erro: any, padrao: string): string {
  const corpo = erro?.error;
  if (!corpo || typeof corpo !== 'object') {
    return padrao;
  }
  const mensagens: string[] = [];
  Object.values(corpo).forEach((valor) => {
    if (Array.isArray(valor)) {
      valor.forEach((item) => typeof item === 'string' && mensagens.push(item));
    } else if (typeof valor === 'string') {
      mensagens.push(valor);
    }
  });
  return mensagens.length ? mensagens.join(' ') : padrao;
}
