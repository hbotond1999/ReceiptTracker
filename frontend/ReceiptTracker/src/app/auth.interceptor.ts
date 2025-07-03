import { Injectable } from '@angular/core';
import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Store } from '@ngrx/store';
import { selectAccessToken } from './store/auth/auth.selectors';
import { take, switchMap } from 'rxjs/operators';

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
          return next.handle(authReq);
        }
        return next.handle(req);
      })
    );
  }
} 