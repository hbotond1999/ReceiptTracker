import { createReducer, on } from '@ngrx/store';
import { AuthState, initialState } from './auth.state';
import * as AuthActions from './auth.actions';

export const authReducer = createReducer(
  initialState,
  
  // Login
  on(AuthActions.login, (state) => ({
    ...state,
    isLoading: true,
    error: null,
  })),
  
  on(AuthActions.loginTokenReceived, (state, { token }) => ({
    ...state,
    token,
    isAuthenticated: true,
    isLoading: true, // Keep loading while fetching user profile
    error: null,
  })),
  
  on(AuthActions.loginSuccess, (state, { token, user }) => ({
    ...state,
    user,
    token,
    isAuthenticated: true,
    isLoading: false,
    error: null,
  })),
  
  on(AuthActions.loginFailure, (state, { error }) => ({
    ...state,
    isLoading: false,
    error,
    isAuthenticated: false,
  })),
  
  // Logout
  on(AuthActions.logout, (state) => ({
    ...state,
    isLoading: true,
  })),
  
  on(AuthActions.logoutSuccess, (state) => ({
    ...state,
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  })),
  
  // Auto Login
  on(AuthActions.autoLogin, (state) => ({
    ...state,
    isLoading: true,
  })),
  
  on(AuthActions.autoLoginFailure, (state) => ({
    ...state,
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
  })),
  
  // Token Refresh
  on(AuthActions.refreshToken, (state) => ({
    ...state,
    isRefreshing: true,
  })),
  
  on(AuthActions.refreshTokenSuccess, (state, { token }) => ({
    ...state,
    token,
    isRefreshing: false,
  })),
  
  on(AuthActions.refreshTokenFailure, (state, { error }) => ({
    ...state,
    isRefreshing: false,
    error,
    isAuthenticated: false,
  })),
  
  // Get Current User
  on(AuthActions.getCurrentUser, (state) => ({
    ...state,
    isLoading: true,
  })),
  
  // Get Current User Profile
  on(AuthActions.getCurrentUserProfile, (state) => ({
    ...state,
    isLoading: true,
  })),
  
  on(AuthActions.getCurrentUserSuccess, (state, { user }) => ({
    ...state,
    user,
    isLoading: false,
  })),
  
  on(AuthActions.getCurrentUserFailure, (state, { error }) => ({
    ...state,
    isLoading: false,
    error,
  }))
); 