import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { Acao, pode, Recurso } from '../security/rbac';


type PermissaoRota = {
  recurso: Recurso;
  acao: Acao;
};


export const permissionGuard: CanActivateFn = (route) => {
  const router = inject(Router);
  const permissao = route.data?.['permission'] as PermissaoRota | undefined;

  if (!permissao || pode(permissao.recurso, permissao.acao)) {
    return true;
  }

  return router.createUrlTree(['/home']);
};
