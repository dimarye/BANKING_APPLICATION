'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { LoginForm } from '@/components/forms/LoginForm';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/contexts/AuthContext';

export default function LoginPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [showRegister, setShowRegister] = useState(false);

  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  const handleLoginSuccess = () => {
    router.push('/dashboard');
  };

  const handleRegisterSuccess = () => {
    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Welcome to Banking App
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            {showRegister ? 'Create your account' : 'Sign in to your account'}
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{showRegister ? 'Create Account' : 'Sign In'}</CardTitle>
            <CardDescription>
              {showRegister 
                ? 'Enter your information to create a new account'
                : 'Enter your credentials to access your account'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {showRegister ? (
              <div className="space-y-4">
                {/* Register form will be imported here */}
                <div className="text-center text-sm text-gray-600">
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => setShowRegister(false)}
                    className="font-medium text-blue-600 hover:text-blue-500"
                  >
                    Sign in
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <LoginForm onSuccess={handleLoginSuccess} />
                <div className="text-center text-sm text-gray-600">
                  Don't have an account?{' '}
                  <button
                    type="button"
                    onClick={() => setShowRegister(true)}
                    className="font-medium text-blue-600 hover:text-blue-500"
                  >
                    Create one
                  </button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="text-center">
          <Link
            href="/"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
