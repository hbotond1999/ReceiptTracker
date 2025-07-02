import { createAction, props } from '@ngrx/store';
import { TokenOut, UserOut } from '../../api/model/models';

// Login Actions
export const login = createAction(
  '[Auth] Login',
  props<{ username: string; password: string }>()
);

export const loginSuccess = createAction(
  '[Auth] Login Success',
  props<{ token: TokenOut; user: UserOut }>()
);

export const loginFailure = createAction(
  '[Auth] Login Failure',
  props<{ error: string }>()
);

// Logout Actions
export const logout = createAction('[Auth] Logout');

export const logoutSuccess = createAction('[Auth] Logout Success');

// Auto Login Actions
export const autoLogin = createAction('[Auth] Auto Login');

export const autoLoginSuccess = createAction(
  '[Auth] Auto Login Success',
  props<{ token: TokenOut; user: UserOut }>()
);

export const autoLoginFailure = createAction('[Auth] Auto Login Failure');

// Token Refresh Actions
export const refreshToken = createAction('[Auth] Refresh Token');

export const refreshTokenSuccess = createAction(
  '[Auth] Refresh Token Success',
  props<{ token: TokenOut }>()
);

export const refreshTokenFailure = createAction(
  '[Auth] Refresh Token Failure',
  props<{ error: string }>()
);

// Get Current User Actions
export const getCurrentUser = createAction('[Auth] Get Current User');

export const getCurrentUserProfile = createAction('[Auth] Get Current User Profile');

export const getCurrentUserSuccess = createAction(
  '[Auth] Get Current User Success',
  props<{ user: UserOut }>()
);

export const getCurrentUserFailure = createAction(
  '[Auth] Get Current User Failure',
  props<{ error: string }>()
); 