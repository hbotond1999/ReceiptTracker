import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { of, from } from 'rxjs';
import { map, mergeMap, catchError, switchMap, tap } from 'rxjs/operators';
import { ApiService } from '../../services/api.service';
import * as AuthActions from './auth.actions';
import * as AuthSelectors from './auth.selectors';
import { Storage } from '@ionic/storage-angular';
import { TokenOut, UserListOut, UserOut } from '../../api/model/models';

@Injectable()
export class AuthEffects {

  constructor(
    private actions$: Actions,
    private authService: ApiService,
    private store: Store,
    private storage: Storage
  ) {}

  // Login Effect
  login$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.login),
      mergeMap(({ username, password }) =>
        this.authService.login(username, password).pipe(
          map((token: TokenOut) => {
            // Store token in local storage
            this.storage.set('access_token', token.access_token);
            this.storage.set('refresh_token', token.refresh_token);

            // Immediately dispatch token received action to store tokens in store
            return AuthActions.loginTokenReceived({ token });
          }),
          catchError(error => of(AuthActions.loginFailure({ error: error.message || 'Login failed' })))
        )
      )
    )
  );

  // Handle token received and fetch user profile
  loginTokenReceived$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.loginTokenReceived),
      mergeMap(({ token }) =>
        this.authService.getCurrentUserProfile().pipe(
          map((user: UserOut) => {
            return AuthActions.loginSuccess({
              token,
              user
            });
          }),
          catchError(error => of(AuthActions.getCurrentUserFailure({ error: error.message || 'Failed to get user info' })))
        )
      )
    )
  );
  
  getCurrentUserProfile$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.getCurrentUserProfile),
      mergeMap(() =>
        from(Promise.all([
          this.storage.get('access_token'),
          this.storage.get('refresh_token')
        ])).pipe(
          switchMap(([accessToken, refreshToken]) =>
            this.authService.getCurrentUserProfile().pipe(
              map((user: UserOut) => {
                return AuthActions.loginSuccess({
                  token: { access_token: accessToken, refresh_token: refreshToken },
                  user
                });
              }),
              catchError(error => of(AuthActions.getCurrentUserFailure({ error: error.message || 'Failed to get user info' })))
            )
          )
        )
      )
    )
  );

  // Auto Login Effect
  autoLogin$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.autoLogin),
      mergeMap(() =>
        from(this.storage.get('refresh_token')).pipe(
          switchMap(refreshToken => {
            if (refreshToken) {
              return this.authService.refreshToken(refreshToken).pipe(
                map((token: TokenOut) => {
                  this.storage.set('access_token', token.access_token);
                  this.storage.set('refresh_token', token.refresh_token);
                  return AuthActions.loginTokenReceived({ token });
                }),
                catchError(() => of(AuthActions.autoLoginFailure()))
              );
            } else {
              return of(AuthActions.autoLoginFailure());
            }
          })
        )
      )
    )
  );

  // Refresh Token Effect
  refreshToken$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.refreshToken),
      mergeMap(() =>
        this.store.select(AuthSelectors.selectRefreshToken).pipe(
          switchMap(refreshToken => {
            if (refreshToken) {
              return this.authService.refreshToken(refreshToken).pipe(
                map((token: TokenOut) => {
                  this.storage.set('access_token', token.access_token);
                  this.storage.set('refresh_token', token.refresh_token);
                  return AuthActions.refreshTokenSuccess({ token });
                }),
                catchError(error => of(AuthActions.refreshTokenFailure({ error: error.message || 'Token refresh failed' })))
              );
            } else {
              return of(AuthActions.refreshTokenFailure({ error: 'No refresh token available' }));
            }
          })
        )
      )
    )
  );

  // Logout Effect
  logout$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.logout),
      tap(() => {
        // Clear stored tokens
        this.storage.remove('access_token');
        this.storage.remove('refresh_token');
      }),
      map(() => AuthActions.logoutSuccess())
    )
  );


}
