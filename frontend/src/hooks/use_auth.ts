// Custom hook for authentication.
'use client';

import { useEffect, useCallback } from 'react';
import { useAuthStore } from '@/store/auth_store';
import { authApi } from '@/lib/api';
import type { User } from '@/schemas/auth';

interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

export function useAuth(): UseAuthReturn {
  const { 
    user, 
    isAuthenticated, 
    isLoading, 
    login: storeLogin, 
    logout: storeLogout,
    initialize 
  } = useAuthStore();

  // Initialize auth state on mount
  useEffect(() => {
    initialize();
  }, [initialize]);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await authApi.getCurrentUser();
      // Update store with fresh user data if needed
    } catch {
      // Token may be expired
      storeLogout();
    }
  }, [storeLogout]);

  return {
    user,
    isAuthenticated,
    isLoading,
    login: storeLogin,
    logout: storeLogout,
    refreshUser,
  };
}

// Hook for protected routes
export function useRequireAuth() {
  const { isAuthenticated, isLoading } = useAuthStore();
  
  return { isAuthenticated, isLoading };
}