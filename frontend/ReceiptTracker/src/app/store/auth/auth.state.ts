import {UserOut} from '../../api/model/userOut';

export interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  expiresAt: number | null; // timestamp (ms)
  userProfile: UserOut | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  register: {
    loading: boolean;
    error: string | null;
    success: boolean;
  };
}

export const initialAuthState: AuthState = {
  accessToken: null,
  refreshToken: null,
  expiresAt: null,
  userProfile: null,
  isAuthenticated: false,
  loading: false,
  error: null,
  register: {
    loading: false,
    error: null,
    success: false,
  },
};
