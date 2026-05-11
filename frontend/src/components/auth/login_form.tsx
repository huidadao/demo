// Login form component.
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/store/auth_store';
import { loginSchema } from '@/schemas/auth';

export function LoginForm() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate with Zod
    const result = loginSchema.safeParse({ email, password });
    
    if (!result.success) {
      // Show all validation errors
      const errors = result.error.errors.map(err => err.message).join(', ');
      toast.error(errors || 'Please check your input');
      return;
    }
    
    setIsSubmitting(true);
    toast.dismiss(); // Clear any existing toasts
    
    try {
      const tokenResponse = await authApi.login(email, password);

      // Save token to localStorage first so getCurrentUser can authenticate
      localStorage.setItem('access_token', tokenResponse.access_token);

      // Fetch actual user data from backend
      const user = await authApi.getCurrentUser();

      login(user, tokenResponse.access_token, tokenResponse.must_change_password);
      toast.success('Login successful!');

      if (tokenResponse.must_change_password) {
        router.push('/change-password');
      } else {
        router.push('/dashboard');
      }
    } catch (error: any) {
      console.log('Login error caught:', error);
      console.log('Error response:', error?.response);
      console.log('Error data:', error?.response?.data);
      
      // Handle different error structures
      let errorMessage = 'Login failed. Please try again.';
      
      // Try to get error message from response
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error?.response?.status === 401) {
        errorMessage = 'Invalid email or password';
      } else if (error?.message) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500"
          placeholder="you@example.com"
        />
      </div>
      
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500"
          placeholder="••••••••"
        />
      </div>
      
      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isSubmitting ? 'Signing in...' : 'Sign In'}
      </button>
    </form>
  );
}