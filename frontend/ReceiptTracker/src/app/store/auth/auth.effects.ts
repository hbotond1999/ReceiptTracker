import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { of, from, timer } from 'rxjs';
import { map, mergeMap, catchError, switchMap, tap, withLatestFrom } from 'rxjs/operators';
import * as AuthActions from './auth.actions';
import * as AuthSelectors from './auth.selectors';
import { AuthService } from '../../api/api/auth.service';
import { TokenOut } from '../../api/model/tokenOut';
import { Storage } from '@ionic/storage-angular';
import { Router } from '@angular/router';

@Injectable()
export class AuthEffects {
  constructor(
    private actions$: Actions,
    private authService: AuthService,
    private storage: Storage,
    private store: Store,
    private router: Router
  ) {}

  // Login effect
  login$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.login),
      mergeMap(({ username, password }) =>
        this.authService.loginAuthLoginPost(username, password).pipe(
          mergeMap((tokenOut: TokenOut) => {
            const expiresIn = 3600; // Ha nincs expires_in mező, default 1 óra
            const expiresAt = Date.now() + (expiresIn * 1000) - 5000;
            return from(Promise.all([
              this.storage.set('accessToken', tokenOut.access_token),
              this.storage.set('refreshToken', tokenOut.refresh_token),
              this.storage.set('expiresAt', expiresAt)
            ])).pipe(
              map(() => AuthActions.loginSuccess({
                accessToken: tokenOut.access_token,
                refreshToken: tokenOut.refresh_token,
                expiresAt
              }))
            );
          }),
          catchError(error => of(AuthActions.loginFailure({ error: error?.error?.detail || 'Login failed' })))
        )
      )
    )
  );

  // LoginSuccess után user profil betöltése
  loginSuccess$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.loginSuccess),
      map(() => AuthActions.loadUserProfile())
    )
  );

  // User profil betöltése
  loadUserProfile$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.loadUserProfile),
      switchMap(() =>
        this.authService.getMeAuthMeGet().pipe(
          map(userProfile => AuthActions.loadUserProfileSuccess({ userProfile })),
          catchError(error => of(AuthActions.loadUserProfileFailure({ error: error?.error?.detail || 'Profile load failed' })))
        )
      )
    )
  );

  // Auto-login effect
  autoLogin$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.autoLogin),
      switchMap(() =>
        from(Promise.all([
          this.storage.get('accessToken'),
          this.storage.get('refreshToken'),
          this.storage.get('expiresAt')
        ])).pipe(
          mergeMap(([accessToken, refreshToken, expiresAt]) => {
            if (accessToken && expiresAt && Date.now() < expiresAt) {
              return of(AuthActions.autoLoginSuccess({ accessToken, refreshToken, expiresAt }));
            } else if (refreshToken) {
              return of(AuthActions.refreshToken());
            } else {
              return of(AuthActions.autoLoginFailure());
            }
          })
        )
      )
    )
  );

  // AutoLoginSuccess után user profil betöltése
  autoLoginSuccess$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.autoLoginSuccess),
      map(() => AuthActions.loadUserProfile())
    )
  );

  // Token refresh effect
  refreshToken$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.refreshToken),
      withLatestFrom(this.store.select(AuthSelectors.selectRefreshToken)),
      switchMap(([_, refreshToken]) => {
        if (!refreshToken) return of(AuthActions.refreshTokenFailure({ error: 'No refresh token' }));
        return this.authService.refreshTokenAuthRefreshPost(refreshToken).pipe(
          mergeMap((tokenOut: TokenOut) => {
            const expiresIn = 3600;
            const expiresAt = Date.now() + (expiresIn * 1000) - 5000;
            return from(Promise.all([
              this.storage.set('accessToken', tokenOut.access_token),
              this.storage.set('refreshToken', tokenOut.refresh_token),
              this.storage.set('expiresAt', expiresAt)
            ])).pipe(
              map(() => AuthActions.refreshTokenSuccess({
                accessToken: tokenOut.access_token,
                refreshToken: tokenOut.refresh_token,
                expiresAt
              }))
            );
          }),
          catchError(error => of(AuthActions.refreshTokenFailure({ error: error?.error?.detail || 'Token refresh failed' })))
        );
      })
    )
  );

  // Token refresh után user profil betöltése
  refreshTokenSuccess$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.refreshTokenSuccess),
      map(() => AuthActions.loadUserProfile())
    )
  );

  // Token expiry figyelése és időzített refresh
  scheduleRefresh$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.loginSuccess, AuthActions.refreshTokenSuccess, AuthActions.autoLoginSuccess),
      switchMap(({ expiresAt }) => {
        const delay = expiresAt - Date.now() - 5000;
        if (delay > 0) {
          return timer(delay).pipe(map(() => AuthActions.refreshToken()));
        } else {
          return of(AuthActions.refreshToken());
        }
      })
    )
  );

  // Logout effect: Storage törlése
  logout$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.logout),
      switchMap(() =>
        from(Promise.all([
          this.storage.remove('accessToken'),
          this.storage.remove('refreshToken'),
          this.storage.remove('expiresAt')
        ])).pipe(
          tap(() => this.router.navigateByUrl('/login')),
          map(() => ({ type: '[Auth] Logout Complete' }))
        )
      )
    ),
    { dispatch: false }
  );
} 