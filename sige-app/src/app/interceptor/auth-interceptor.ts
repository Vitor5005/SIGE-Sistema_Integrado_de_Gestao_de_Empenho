import {
  HttpInterceptorFn,
  HttpErrorResponse
} from '@angular/common/http';

import { inject } from '@angular/core';
import { Auth } from '../service/auth';

import {
  catchError,
  switchMap,
  throwError
} from 'rxjs';
import { Router } from '@angular/router';

export const authInterceptor: HttpInterceptorFn = (req, next) => {

  const authService = inject(Auth);
  const router = inject(Router);

  const token = authService.getAccessToken();

  let request = req;

  if (token) {

    request = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });

  }

  return next(request).pipe(

    catchError((error: HttpErrorResponse) => {

      if (error.status === 401) {

        return authService.refreshToken().pipe(

          switchMap((res: any) => {

            authService.salvarToken(res.access, res.refresh);

            const newReq = req.clone({
              setHeaders: {
                Authorization: `Bearer ${res.access}`
              }
            });

            return next(newReq);

          }),

          catchError(() => {
            authService.logout();
            router.navigate(['/login']);
            return throwError(() => error);
          })

        );

      }

      return throwError(() => error);

    })

  );

};