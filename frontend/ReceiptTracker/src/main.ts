import {bootstrapApplication} from '@angular/platform-browser';
import {PreloadAllModules, provideRouter, RouteReuseStrategy, withPreloading} from '@angular/router';
import {IonicRouteStrategy, provideIonicAngular} from '@ionic/angular/standalone';
import {HTTP_INTERCEPTORS, provideHttpClient, withInterceptorsFromDi} from '@angular/common/http';
import {provideApi} from './app/api/provide-api';
import {environment} from './environments/environment';
import {routes} from './app/app.routes';
import {AppComponent} from './app/app.component';
import {defineCustomElements} from '@ionic/pwa-elements/loader';
import {provideStore} from '@ngrx/store';
import {provideEffects} from '@ngrx/effects';
import {authReducer} from './app/store/auth/auth.reducer';
import {AuthEffects} from './app/store/auth/auth.effects';
import {AuthInterceptor} from './app/auth.interceptor';
import {Storage} from '@ionic/storage-angular';
import {provideStoreDevtools} from '@ngrx/store-devtools';
import {ModalController} from "@ionic/angular";

// Ionic Storage init
const storage = new Storage();
storage.create();

defineCustomElements(window);
bootstrapApplication(AppComponent, {
  providers: [
    ModalController,
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    provideIonicAngular(),
    provideRouter(routes, withPreloading(PreloadAllModules)),
    provideHttpClient(
      withInterceptorsFromDi(),
    ),
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true,
    },
    provideApi(environment.apiUrl),
    provideStore({ auth: authReducer }),
    provideEffects([AuthEffects]),
    provideStoreDevtools({ maxAge: 25, logOnly: !environment.production }),
    { provide: Storage, useValue: storage }
  ],
});
