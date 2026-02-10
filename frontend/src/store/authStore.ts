import { create } from 'zustand';
import api from '../config/api';

interface User {
  id: string;
  email: string;
  role: 'admin' | 'assistant' | 'finance' | 'driver';
  first_name: string;
  last_name: string;
  phone?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  tempToken: string | null;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  verify2FA: (code: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  tempToken: null,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.post('/auth/login', { email, password });
      set({ tempToken: data.temp_token, isLoading: false });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Login failed',
        isLoading: false,
      });
      throw err;
    }
  },

  verify2FA: async (code) => {
    const { tempToken } = get();
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.post('/auth/verify-2fa', {
        temp_token: tempToken,
        code,
      });
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      set({ isAuthenticated: true, tempToken: null, isLoading: false });
      // Load user profile
      await get().loadUser();
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Invalid 2FA code',
        isLoading: false,
      });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, isAuthenticated: false, tempToken: null, error: null });
  },

  loadUser: async () => {
    // We don't have a /me endpoint yet, so decode JWT to get user_id
    // For now, just mark as authenticated if token exists
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isAuthenticated: false, user: null });
      return;
    }
    try {
      // Decode JWT payload (base64)
      const payload = JSON.parse(atob(token.split('.')[1]));
      set({
        isAuthenticated: true,
        user: {
          id: payload.sub,
          email: payload.email || '',
          role: payload.role || 'driver',
          first_name: payload.first_name || '',
          last_name: payload.last_name || '',
        },
      });
    } catch {
      set({ isAuthenticated: false, user: null });
    }
  },

  clearError: () => set({ error: null }),
}));
