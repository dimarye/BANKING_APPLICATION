'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { useAuth } from '@/contexts/AuthContext';

export default function Home() {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">SecureBank</h1>
            </div>
            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <>
                  <span className="text-sm text-gray-700">
                    Welcome, {user?.first_name}
                  </span>
                  <Link href="/dashboard">
                    <Button>Dashboard</Button>
                  </Link>
                </>
              ) : (
                <>
                  <Link href="/auth/login">
                    <Button variant="outline">Sign In</Button>
                  </Link>
                  <Link href="/auth/login">
                    <Button>Get Started</Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
            Modern Banking
            <span className="block text-blue-600">Made Simple</span>
          </h1>
          <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
            Experience secure, fast, and intelligent banking with real-time updates, 
            instant transfers, and comprehensive financial management tools.
          </p>
          <div className="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8">
            <div className="rounded-md shadow">
              <Link href="/auth/login">
                <Button size="lg" className="w-full">
                  Open Account
                </Button>
              </Link>
            </div>
            <div className="mt-3 rounded-md shadow sm:mt-0 sm:ml-3">
              <Link href="/auth/login">
                <Button variant="outline" size="lg" className="w-full">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="lg:text-center">
          <h2 className="text-base font-semibold tracking-wide uppercase text-blue-600">
            Features
          </h2>
          <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">
            Everything you need for modern banking
          </p>
        </div>

        <div className="mt-10">
          <div className="space-y-10 md:space-y-0 md:grid md:grid-cols-2 md:gap-x-8 md:gap-y-10">
            {/* Feature 1 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white mr-4">
                    <span className="text-xl">💰</span>
                  </div>
                  Real-time Balance Updates
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  See your account balances update instantly with every transaction. 
                  No more waiting for refreshes or manual updates.
                </CardDescription>
              </CardContent>
            </Card>

            {/* Feature 2 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <div className="flex items-center justify-center h-12 w-12 rounded-md bg-green-500 text-white mr-4">
                    <span className="text-xl">🚀</span>
                  </div>
                  Instant Transfers
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Send money to anyone, anywhere, in seconds. 
                  Our advanced infrastructure ensures your transfers are fast and secure.
                </CardDescription>
              </CardContent>
            </Card>

            {/* Feature 3 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <div className="flex items-center justify-center h-12 w-12 rounded-md bg-purple-500 text-white mr-4">
                    <span className="text-xl">🔒</span>
                  </div>
                  Advanced Security
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Bank-grade encryption, fraud detection, and real-time alerts 
                  keep your money safe 24/7.
                </CardDescription>
              </CardContent>
            </Card>

            {/* Feature 4 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <div className="flex items-center justify-center h-12 w-12 rounded-md bg-orange-500 text-white mr-4">
                    <span className="text-xl">📱</span>
                  </div>
                  Mobile First Design
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Access your accounts from any device. Our responsive design 
                  works perfectly on desktop, tablet, and mobile.
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-blue-600">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-white">
              Ready to get started?
            </h2>
            <p className="mt-4 text-lg text-blue-100">
              Join thousands of users who trust SecureBank for their financial needs.
            </p>
            <div className="mt-8">
              <Link href="/auth/login">
                <Button size="lg" variant="secondary">
                  Open Your Account Today
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
          <div className="text-center text-gray-500">
            <p>&copy; 2024 SecureBank. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
