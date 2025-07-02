import { UserOut, TokenOut } from '../../api/model/models';

export interface AuthState {
  user: UserOut | null;
  token: TokenOut | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  isRefreshing: boolean;
}

export const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  isRefreshing: false,
}; 