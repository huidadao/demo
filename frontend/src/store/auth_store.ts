// Zustand store for authentication state.
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  email: string;
  created_at: string;
  updated_at: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  mustChangePassword: boolean;

  // Actions
  setUser: (user: User | null) => void;
  setAccessToken: (token: string | null) => void;
  setLoading: (loading: boolean) => void;
  login: (user: User, token: string, mustChangePassword?: boolean) => void;
  logout: () => void;
  initialize: () => void;
  clearMustChangePassword: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      mustChangePassword: false,

      setUser: (user) => set({ user, isAuthenticated: !!user }),

      setAccessToken: (token) => set({ accessToken: token }),

      setLoading: (isLoading) => set({ isLoading }),

      login: (user, token, mustChangePassword = false) => {
        localStorage.setItem('access_token', token);
        localStorage.setItem('user', JSON.stringify(user));
        localStorage.setItem('must_change_password', String(mustChangePassword));
        set({
          user,
          accessToken: token,
          isAuthenticated: true,
          isLoading: false,
          mustChangePassword,
        });
      },

      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        localStorage.removeItem('must_change_password');
        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
          isLoading: false,
          mustChangePassword: false,
        });
      },

      initialize: () => {
        if (typeof window === 'undefined') {
          set({ isLoading: false });
          return;
        }

        const token = localStorage.getItem('access_token');
        const userStr = localStorage.getItem('user');
        const mustChangeStr = localStorage.getItem('must_change_password');

        if (token && userStr) {
          try {
            const user = JSON.parse(userStr);
            set({
              user,
              accessToken: token,
              isAuthenticated: true,
              isLoading: false,
              mustChangePassword: mustChangeStr === 'true',
            });
          } catch {
            set({ isLoading: false });
          }
        } else {
          set({ isLoading: false });
        }
      },

      clearMustChangePassword: () => {
        localStorage.removeItem('must_change_password');
        set({ mustChangePassword: false });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        isAuthenticated: state.isAuthenticated,
        mustChangePassword: state.mustChangePassword,
      }),
    }
  )
);