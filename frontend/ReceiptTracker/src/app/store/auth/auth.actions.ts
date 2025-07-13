import {createAction, props} from '@ngrx/store';
import {UserOut} from '../../api/model/userOut';
import {PublicUserRegister} from '../../api/model/publicUserRegister';

export const login = createAction('[Auth] Login', props<{ username: string; password: string }>());
export const loginSuccess = createAction('[Auth] Login Success', props<{ accessToken: string; refreshToken: string; expiresAt: number }>());
export const loginFailure = createAction('[Auth] Login Failure', props<{ error: string }>());

export const biometricLogin = createAction('[Auth] Biometric Login');
export const biometricLoginSuccess = createAction('[Auth] Biometric Login Success', props<{ accessToken: string; refreshToken: string; expiresAt: number }>());
export const biometricLoginFailure = createAction('[Auth] Biometric Login Failure', props<{ error: string }>());

export const enableBiometric = createAction('[Auth] Enable Biometric', props<{ username: string; password: string }>());
export const enableBiometricSuccess = createAction('[Auth] Enable Biometric Success');
export const enableBiometricFailure = createAction('[Auth] Enable Biometric Failure', props<{ error: string }>());

export const logout = createAction('[Auth] Logout');

export const loadUserProfile = createAction('[Auth] Load User Profile');
export const loadUserProfileSuccess = createAction('[Auth] Load User Profile Success', props<{ userProfile: UserOut }>());
export const loadUserProfileFailure = createAction('[Auth] Load User Profile Failure', props<{ error: string }>());

export const refreshToken = createAction('[Auth] Refresh Token');
export const refreshTokenSuccess = createAction('[Auth] Refresh Token Success', props<{ accessToken: string; refreshToken: string; expiresAt: number }>());
export const refreshTokenFailure = createAction('[Auth] Refresh Token Failure', props<{ error: string }>());

export const autoLogin = createAction('[Auth] Auto Login');
export const autoLoginSuccess = createAction('[Auth] Auto Login Success', props<{ accessToken: string; refreshToken: string; expiresAt: number }>());
export const autoLoginFailure = createAction('[Auth] Auto Login Failure');

// Registration actions
export const register = createAction('[Auth] Register', props<{ userData: PublicUserRegister }>());
export const registerSuccess = createAction('[Auth] Register Success', props<{ userProfile: UserOut }>());
export const registerFailure = createAction('[Auth] Register Failure', props<{ error: string }>());
