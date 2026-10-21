import { ApplicationConfig, LOCALE_ID, provideZoneChangeDetection } from '@angular/core'; // Adicione aqui
import { registerLocaleData } from '@angular/common';
import localePt from '@angular/common/locales/pt';
import { provideRouter, RouteReuseStrategy } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { routes } from './app.routes';
import { authInterceptor } from './interceptor/auth-interceptor';
import { IdRouteReuseStrategy } from './routing/id-route-reuse.strategy';

registerLocaleData(localePt);

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    { provide: RouteReuseStrategy, useClass: IdRouteReuseStrategy },
    provideHttpClient(withInterceptors([authInterceptor])),
    {
      provide: LOCALE_ID,
      useValue: 'pt-BR'
    }
  ]
  
};
