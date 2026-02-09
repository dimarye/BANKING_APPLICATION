'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/contexts/AuthContext';

interface NavigationProps {
  currentPage?: string;
}

export function Navigation({ currentPage }: NavigationProps) {
  const { user, isAuthenticated, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', active: currentPage === 'dashboard' },
    { href: '/transfer', label: 'Transfer', active: currentPage === 'transfer' },
    { href: '/history', label: 'History', active: currentPage === 'history' },
  ];

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link href="/dashboard">
              <h1 className="text-xl font-bold text-gray-900 hover:text-blue-600 transition-colors">
                SecureBank
              </h1>
            </Link>
            
            {isAuthenticated && (
              <div className="hidden md:flex space-x-1">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      item.active
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <span className="text-sm text-gray-700 hidden sm:block">
                  {user?.first_name} {user?.last_name}
                </span>
                <Button variant="outline" onClick={handleLogout}>
                  Logout
                </Button>
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
  );
}
