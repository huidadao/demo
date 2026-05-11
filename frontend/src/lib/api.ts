// Axios API client with auth interceptors.
import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';

// Create axios instance - use relative path for Next.js proxy
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle 401 errors (only for authenticated requests)
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Only redirect if it's a 401 AND we have a token (meaning session expired)
    if (error.response?.status === 401) {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      if (token && typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        // Only redirect if not on login page
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth API functions
export const authApi = {
  register: async (email: string, password: string) => {
    const response = await api.post('/auth/register', { email, password });
    return response.data;
  },

  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  updateCurrentUser: async (email: string) => {
    const response = await api.put('/auth/me', { email });
    return response.data;
  },

  getStats: async () => {
    const response = await api.get('/auth/stats');
    return response.data;
  },
};