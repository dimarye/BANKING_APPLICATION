'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient, BankAccount } from '@/lib/api';
import { TransferForm } from '@/components/forms/TransferForm';
import { Button } from '@/components/ui/Button';
import { LoadingState } from '@/components/ui/LoadingState';
import { Navigation } from '@/components/layout/Navigation';
import Link from 'next/link';

export default function TransferPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [isLoadingAccounts, setIsLoadingAccounts] = useState(true);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [isLoading, isAuthenticated, router]);

  // Load accounts when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadAccounts();
    }
  }, [isAuthenticated]);

  const loadAccounts = async () => {
    try {
      setIsLoadingAccounts(true);
      const accountsData = await apiClient.getBankAccounts();
      setAccounts(accountsData);
    } catch (error) {
      console.error('Failed to load accounts:', error);
    } finally {
      setIsLoadingAccounts(false);
    }
  };

  const handleTransferSuccess = () => {
    // Refresh accounts to show updated balances
    loadAccounts();
  };

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="flex items-center justify-center" style={{ minHeight: 'calc(100vh - 64px)' }}>
          <LoadingState message="Loading..." />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation currentPage="transfer" />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Transfer Money</h2>
          <p className="text-gray-600">Send money to other accounts instantly</p>
        </div>

        {isLoadingAccounts ? (
          <LoadingState message="Loading your accounts..." />
        ) : (
          <div className="space-y-8">
            {/* Transfer Form */}
            <TransferForm 
              accounts={accounts} 
              onSuccess={handleTransferSuccess}
            />

            {/* Quick Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-blue-900 mb-2">💡 Transfer Tips</h3>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Double-check the recipient account number</li>
                  <li>• Ensure you have sufficient funds</li>
                  <li>• Add a description for easy identification</li>
                  <li>• Transfers are instant and irreversible</li>
                </ul>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-green-900 mb-2">🔒 Security Features</h3>
                <ul className="text-sm text-green-800 space-y-1">
                  <li>• All transfers are encrypted</li>
                  <li>• Real-time fraud detection</li>
                  <li>• Instant notifications for all transfers</li>
                  <li>• 24/7 transaction monitoring</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
