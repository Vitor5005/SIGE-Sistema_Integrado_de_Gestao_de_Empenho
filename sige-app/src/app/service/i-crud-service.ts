import { Observable } from "rxjs";

export interface ICrudService<T> {
    apiUrl: string;
    get(termobusca?: string): Observable<T[]>;
    getById(id: number): Observable<T>;
    save(item: T): Observable<T>;
    delete(id: number): Observable<void>;
}