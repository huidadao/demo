'use client';

import { useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { authApi } from '@/lib/api';
import toast from 'react-hot-toast';

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || '';
  const optionsParam = searchParams.get('options');
  const [options, setOptions] = useState<string[]>(
    optionsParam ? JSON.parse(optionsParam) : []
  );
  const [loading, setLoading] = useState(false);
  const [verified, setVerified] = useState(false);

  const handleVerify = async (code: string) => {
    if (!email) return;

    setLoading(true);
    try {
      await authApi.verifyEmail(email, code);
      setVerified(true);
      toast.success('Email verified successfully!');
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      toast.error(detail || 'Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!email) return;

    setLoading(true);
    try {
      const response = await authApi.resendVerification(email);
      if (response.verification_options) {
        setOptions(response.verification_options);
      }
      toast.success('New verification code sent!');
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      toast.error(detail || 'Failed to resend code.');
    } finally {
      setLoading(false);
    }
  };

  if (verified) {
    return (
      <div className="text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Email Verified!</h2>
        <p className="text-gray-600 mb-6">Your email has been successfully verified.</p>
        <button
          onClick={() => router.push('/login')}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
        >
          Go to Login
        </button>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-center text-gray-900 mb-2">
        Verify Your Email
      </h1>
      <p className="text-center text-gray-600 mb-6">
        We sent a verification code to <span className="font-semibold">{email}</span>.
        <br />
        Please click the correct number below.
      </p>

      <div className="flex justify-center gap-4 mb-6">
        {options.map((code, index) => (
          <button
            key={index}
            onClick={() => handleVerify(code)}
            disabled={loading}
            className="w-20 h-20 bg-blue-50 border-2 border-blue-200 rounded-lg flex items-center justify-center text-2xl font-bold text-blue-700 hover:bg-blue-100 hover:border-blue-400 active:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {code}
          </button>
        ))}
      </div>

      <div className="text-center">
        <button
          onClick={handleResend}
          disabled={loading}
          className="text-sm text-blue-600 hover:underline disabled:opacity-50"
        >
          Didn't receive the code? Resend
        </button>
      </div>

      <p className="mt-4 text-center text-sm text-gray-500">
        The code will expire in 30 minutes.
      </p>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md p-8 bg-white rounded-lg shadow-md">
        <Suspense fallback={<div className="text-center">Loading...</div>}>
          <VerifyEmailContent />
        </Suspense>
      </div>
    </main>
  );
}
