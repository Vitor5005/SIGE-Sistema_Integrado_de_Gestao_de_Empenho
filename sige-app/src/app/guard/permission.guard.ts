import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { Acao, pode, Recurso } from '../security/rbac';
import { FeedbackService } from '../service/feedback.service';


type PermissaoRota = {
  recurso: Recurso;
  acao: Acao;
};


export const permissionGuard: CanActivateFn = (route) => {
  const router = inject(Router);
  const feedback = inject(FeedbackService);
  const permissao = route.data?.['permission'] as PermissaoRota | undefined;

  if (!permissao || pode(permissao.recurso, permissao.acao)) {
    return true;
  }

  feedback.aviso('Você não possui permissão para acessar esta página.');
  return router.createUrlTree(['/home']);
};
