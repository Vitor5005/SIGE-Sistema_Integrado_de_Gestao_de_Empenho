import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';

function parseJwt(token: string): any {
  const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
  const json = decodeURIComponent(
    atob(base64).split('').map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join('')
  );
  return JSON.parse(json);
}

export const authGuard: CanActivateFn = (route) => {
  const router = inject(Router);
  const token = localStorage.getItem('access_token');
  if (!token) return router.createUrlTree(['/login']);

  const requiredRoles = route.data?.['roles'] as string[] | undefined;
  if (!requiredRoles?.length) return true;

  try {
    const payload = parseJwt(token);
    const papel = payload?.papel;
    return requiredRoles.includes(papel) ? true : router.createUrlTree(['/home']);
  } catch {
    return router.createUrlTree(['/login']);
  }
};