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
import { NativeBiometric, BiometricOptions } from 'capacitor-native-biometric';

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

  // Register effect
  register$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.register),
      mergeMap(({ userData }) =>
        this.authService.registerUserPublicAuthRegisterPublicPost(userData).pipe(
          mergeMap(userProfile => {
            // Sikeres regisztráció után automatikus bejelentkezés
            return this.authService.loginAuthLoginPost(userData.username, userData.password).pipe(
              mergeMap((tokenOut: TokenOut) => {
                const expiresIn = 3600;
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
              })
            );
          }),
          catchError(error => {
            console.error('Registration error:', error);
            const errorMessage = error?.error?.detail || 'Registration failed';

            return of(AuthActions.registerFailure({ error: errorMessage }));
          })
        )
      )
    )
  );

  // Enable biometric authentication
  enableBiometric$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.enableBiometric),
      mergeMap(({ username, password }) =>
        from(NativeBiometric.setCredentials({
          username,
          password,
          server: 'ReceiptTracker'
        })).pipe(
          map(() => AuthActions.enableBiometricSuccess()),
          catchError(error => of(AuthActions.enableBiometricFailure({
            error: error?.message || 'Biometric setup failed'
          })))
        )
      )
    )
  );

  // Biometric login effect
  biometricLogin$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.biometricLogin),
      mergeMap(() =>
        from(NativeBiometric.verifyIdentity({
          reason: 'Bejelentkezés biometrikus azonosítással',
          title: 'Biometrikus azonosítás',
          subtitle: 'Használja ujjlenyomatát vagy arcfelismerést a bejelentkezéshez',
          description: 'Helyezze ujját a szenzorra vagy nézzen a kamerába'
        } as BiometricOptions)).pipe(
          mergeMap(() =>
            from(NativeBiometric.getCredentials({
              server: 'ReceiptTracker'
            })).pipe(
              mergeMap(credentials =>
                this.authService.loginAuthLoginPost(credentials.username, credentials.password).pipe(
                  mergeMap((tokenOut: TokenOut) => {
                    const expiresIn = 3600;
                    const expiresAt = Date.now() + (expiresIn * 1000) - 5000;
                    return from(Promise.all([
                      this.storage.set('accessToken', tokenOut.access_token),
                      this.storage.set('refreshToken', tokenOut.refresh_token),
                      this.storage.set('expiresAt', expiresAt)
                    ])).pipe(
                      map(() => AuthActions.biometricLoginSuccess({
                        accessToken: tokenOut.access_token,
                        refreshToken: tokenOut.refresh_token,
                        expiresAt
                      }))
                    );
                  }),
                  catchError(error => of(AuthActions.biometricLoginFailure({
                    error: error?.error?.detail || 'Biometric login failed'
                  })))
                )
              )
            )
          ),
          catchError(error => of(AuthActions.biometricLoginFailure({
            error: error?.message || 'Biometric verification failed'
          })))
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

  // BiometricLoginSuccess után user profil betöltése
  biometricLoginSuccess$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.biometricLoginSuccess),
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
            const now = Date.now();
            const isTokenExpired = !expiresAt || now >= expiresAt;

            // Ha van érvényes access token és nem járt le
            if (accessToken && !isTokenExpired) {
              return of(AuthActions.autoLoginSuccess({ accessToken, refreshToken, expiresAt }));
            }
            // Ha lejárt az access token, de van refresh token, akkor frissítjük
            else if (isTokenExpired && refreshToken) {
              console.log('Access token expired, attempting refresh...');
              return of(AuthActions.refreshToken());
            }
            // Ha nincs refresh token vagy access token, akkor auto-login sikertelen
            else {
              console.log('No valid tokens found for auto-login');
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
          catchError(error => {
            console.log('Token refresh failed:', error);
            return of(AuthActions.refreshTokenFailure({ error: error?.error?.detail || 'Token refresh failed' }));
          })
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

  // Token refresh failure kezelése - logout ha refresh sikertelen
  refreshTokenFailure$ = createEffect(() =>
    this.actions$.pipe(
      ofType(AuthActions.refreshTokenFailure),
      tap(() => {
        console.log('Token refresh failed, logging out...');
        this.store.dispatch(AuthActions.logout());
      })
    ),
    { dispatch: false }
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

  // Logout effect: Storage törlése (biometric credentials are kept)
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
