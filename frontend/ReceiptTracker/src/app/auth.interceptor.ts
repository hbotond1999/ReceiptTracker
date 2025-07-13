import {Injectable} from '@angular/core';
import {HttpErrorResponse, HttpEvent, HttpHandler, HttpInterceptor, HttpRequest} from '@angular/common/http';
import {Observable, throwError} from 'rxjs';
import {Store} from '@ngrx/store';
import {selectAccessToken} from './store/auth/auth.selectors';
import {catchError, switchMap, take} from 'rxjs/operators';
import * as AuthActions from './store/auth/auth.actions';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private store: Store) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Kivételek: login, refresh endpointok
    const isAuthEndpoint = req.url.includes('/auth/login') || req.url.includes('/auth/refresh');
    if (isAuthEndpoint) {
      return next.handle(req);
    }
    return this.store.select(selectAccessToken).pipe(
      take(1),
      switchMap((token: string | null) => {
        if (token) {
          const authReq = req.clone({
            setHeaders: { Authorization: `Bearer ${token}` }
          });
          return next.handle(authReq).pipe(
            catchError((error: HttpErrorResponse) => {
              if (error.status === 401 || error.status === 403) {
                // Automatikus logout 401-es hibánál
                this.store.dispatch(AuthActions.logout());
              }
              return throwError(() => error);
            })
          );
        }
        return next.handle(req).pipe(
          catchError((error: HttpErrorResponse) => {
            if (error.status === 401 || error.status === 403) {
              // Automatikus logout 401-es hibánál
              this.store.dispatch(AuthActions.logout());
            }
            return throwError(() => error);
          })
        );
      })
    );
  }
}
