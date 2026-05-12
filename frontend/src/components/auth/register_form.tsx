// Register form component with email verification.
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { authApi } from '@/lib/api';
import { registerSchema } from '@/schemas/auth';

export function RegisterForm() {
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate with Zod
    const result = registerSchema.safeParse({ email, password, confirmPassword });

    if (!result.success) {
      const errors = result.error.errors.map(err => err.message).join(', ');
      toast.error(errors || 'Please check your input');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await authApi.register(email, password);

      toast.success('Account created! Please verify your email.');
      // Navigate to verification page with email and options
      const searchParams = new URLSearchParams();
      searchParams.set('email', response.email);
      searchParams.set('options', JSON.stringify(response.verification_options));
      router.push(`/verify-email?${searchParams.toString()}`);
    } catch (error: unknown) {
      let errorMessage = 'Registration failed';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } };
        errorMessage = axiosError.response?.data?.detail || errorMessage;
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
          required
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
          required
        />
      </div>

      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
          Confirm Password
        </label>
        <input
          id="confirmPassword"
          name="confirmPassword"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500"
          placeholder="••••••••"
          required
        />
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isSubmitting ? 'Creating account...' : 'Create Account'}
      </button>
    </form>
  );
}
