import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, filter, take, switchMap } from 'rxjs/operators';
import { Store } from '@ngrx/store';
import { selectAccessToken, selectIsRefreshing } from '../store/auth/auth.selectors';
import * as AuthActions from '../store/auth/auth.actions';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private isRefreshing = false;
  private refreshTokenSubject: BehaviorSubject<any> = new BehaviorSubject<any>(null);

  constructor(private store: Store) {}

   intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Skip token for auth endpoints
    if (request.url.includes('/auth/login') || request.url.includes('/auth/register')) {
      return next.handle(request);
    }

    return this.store.select(selectAccessToken).pipe(
      take(1),
      switchMap(token => {
        if (token) {
          request = this.addToken(request, token);
        }
        return next.handle(request).pipe(
          catchError((error: HttpErrorResponse) => {
            if (error.status === 401 && !request.url.includes('/auth/refresh')) {
              return this.handle401Error(request, next);
            }
            return throwError(() => error);
          })
        );
      })
    );
  }

  private addToken(request: HttpRequest<any>, token: string): HttpRequest<any> {
      return request.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      });
    }

  private handle401Error(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    if (!this.isRefreshing) {
      this.isRefreshing = true;
      this.refreshTokenSubject.next(null);

      this.store.dispatch(AuthActions.refreshToken());

      return this.store.select(selectAccessToken).pipe(
        filter(token => token !== null),
        take(1),
        switchMap(token => {
          this.isRefreshing = false;
          this.refreshTokenSubject.next(token);
          return next.handle(this.addToken(request, token!));
        }),
        catchError((err) => {
          this.isRefreshing = false;
          this.store.dispatch(AuthActions.logout());
          return throwError(() => err);
        })
      );
    } else {
      return this.refreshTokenSubject.pipe(
        filter(token => token !== null),
        take(1),
        switchMap(token => next.handle(this.addToken(request, token)))
      );
    }
  }
}
