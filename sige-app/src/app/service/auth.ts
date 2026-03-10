import { Injectable } from '@angular/core';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Token } from '../model/token';

@Injectable({
  providedIn: 'root',
})
export class Auth 
{
  
  apiUrl = environment.API_URL + "/login/";

  constructor(
    private http: HttpClient
  ) { }

  login(username: string, password: string): Observable<Token> {
    return this.http.post<Token>(this.apiUrl, {username, password });
  }

  verifyToken(token: string): Observable<any> {
    let url = environment.API_URL + "verify/";
    return this.http.post(url, { token });
  }

  refreshToken() {

    let url = environment.API_URL + "refresh/";
    const refresh = localStorage.getItem('refresh_token');

    return this.http.post(url, { refresh });

    
  }

  salvarToken(access: string, refresh: string) {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
  }

  getAccessToken(){
    return localStorage.getItem('access_token');
  }


  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

}
