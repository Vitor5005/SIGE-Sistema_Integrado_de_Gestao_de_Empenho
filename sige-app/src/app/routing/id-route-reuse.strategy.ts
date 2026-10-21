import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, BaseRouteReuseStrategy } from '@angular/router';

/**
 * As telas de detalhe (empenho, ata, cardápio...) leem o `?id=` uma única vez no ngOnInit.
 * Por padrão o Angular reaproveita o componente ao navegar para a mesma rota com outro id
 * (ex.: clicar numa notificação de outro empenho estando em um empenho), e a tela não recarrega.
 * Aqui o componente é recriado sempre que o `id` muda.
 */
@Injectable()
export class IdRouteReuseStrategy extends BaseRouteReuseStrategy {
  private recriarTela = false;

  /** Faz a próxima navegação recriar a tela mesmo que a URL seja a atual (ex.: notificação da tela aberta). */
  recriarNaProximaNavegacao(): void {
    this.recriarTela = true;
  }

  override shouldReuseRoute(future: ActivatedRouteSnapshot, curr: ActivatedRouteSnapshot): boolean {
    if (this.recriarTela && future.routeConfig && future.component) {
      this.recriarTela = false;
      return false;
    }

    return super.shouldReuseRoute(future, curr)
      && future.queryParamMap.get('id') === curr.queryParamMap.get('id');
  }
}
