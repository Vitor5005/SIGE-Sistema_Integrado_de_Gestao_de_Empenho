import { Observable } from "rxjs";

export interface ICrudService<T> {
    apiUrl: string;
    get(termobusca?: string, page?: number, pageSize?: number, filtros?: any): Observable<any>;
    getById(id: number): Observable<T>;
    save(item: any): Observable<any>;
    delete(id: number): Observable<void>;
    patch(id: number, object: any): Observable<any> 
}