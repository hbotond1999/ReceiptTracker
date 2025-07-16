import {createFeatureSelector, createSelector} from '@ngrx/store';
import {AuthState} from './auth.state';

export const selectAuthState = createFeatureSelector<AuthState>('auth');
export const selectAccessToken = createSelector(selectAuthState, (state) => state.accessToken);
export const selectRefreshToken = createSelector(selectAuthState, (state) => state.refreshToken);
export const selectExpiresAt = createSelector(selectAuthState, (state) => state.expiresAt);
export const selectUserProfile = createSelector(selectAuthState, (state) => state.userProfile);
export const selectIsAuthenticated = createSelector(selectAuthState, (state) => state.isAuthenticated);
export const selectAuthLoading = createSelector(selectAuthState, (state) => state.loading);
export const selectAuthError = createSelector(selectAuthState, (state) => state.error);
export const selectRegister = createSelector(selectAuthState, (state) => state.register);

// Selector that indicates when the auth process is completely finished
export const selectAuthComplete = createSelector(
  selectAuthLoading,
  selectIsAuthenticated,
  selectUserProfile,
  (loading, isAuthenticated, userProfile) => {
    // Auth is complete when:
    // 1. Not loading
    // 2. Either not authenticated OR (authenticated AND user profile is loaded)
    return !loading && (!isAuthenticated || (isAuthenticated && userProfile !== null));
  }
);
