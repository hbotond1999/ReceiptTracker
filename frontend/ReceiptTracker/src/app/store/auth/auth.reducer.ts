import { createReducer, on } from '@ngrx/store';
import { initialAuthState, AuthState } from './auth.state';
import * as AuthActions from './auth.actions';

export const authReducer = createReducer(
  initialAuthState,
  on(AuthActions.login, (state) => ({ ...state, loading: true, error: null })),
  on(AuthActions.loginSuccess, (state, { accessToken, refreshToken, expiresAt }) => ({
    ...state,
    accessToken,
    refreshToken,
    expiresAt,
    isAuthenticated: true,
    loading: false,
    error: null,
  })),
  on(AuthActions.loginFailure, (state, { error }) => ({ ...state, loading: false, error })),
  on(AuthActions.logout, () => initialAuthState),
  on(AuthActions.loadUserProfileSuccess, (state, { userProfile }) => ({ ...state, userProfile })),
  on(AuthActions.loadUserProfileFailure, (state, { error }) => ({ ...state, error })),
  on(AuthActions.refreshTokenSuccess, (state, { accessToken, refreshToken, expiresAt }) => ({
    ...state,
    accessToken,
    refreshToken,
    expiresAt,
    isAuthenticated: true,
    loading: false,
    error: null,
  })),
  on(AuthActions.refreshTokenFailure, (state, { error }) => ({ ...state, loading: false, error, isAuthenticated: false })),
  on(AuthActions.autoLogin, (state) => ({ ...state, loading: true, error: null })),
  on(AuthActions.autoLoginSuccess, (state, { accessToken, refreshToken, expiresAt }) => ({
    ...state,
    accessToken,
    refreshToken,
    expiresAt,
    isAuthenticated: true,
    loading: false,
    error: null,
  })),
  on(AuthActions.autoLoginFailure, () => ({ ...initialAuthState, loading: false }))
);
