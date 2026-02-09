'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient, BankAccount, Transaction } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingState } from '@/components/ui/LoadingState';
import { EmptyState } from '@/components/ui/EmptyState';
import { Navigation } from '@/components/layout/Navigation';
import { formatCurrency, formatDate, formatAccountNumber, getAccountStatusColor, getTransactionStatusColor } from '@/lib/utils';

export default function Dashboard() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(true);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [isLoading, isAuthenticated, router]);

  // Load data when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  const loadData = async () => {
    try {
      setIsLoadingData(true);
      const [accountsData, transactionsData] = await Promise.all([
        apiClient.getBankAccounts(),
        apiClient.getTransactions({ page_size: 5 })
      ]);
      setAccounts(accountsData);
      setTransactions(transactionsData.results);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoadingData(false);
    }
  };

  const handleLogout = async () => {
    await apiClient.logout();
    router.push('/');
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
      <Navigation currentPage="dashboard" />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-gray-600">Manage your accounts and transactions</p>
        </div>

        {isLoadingData ? (
          <LoadingState message="Loading your data..." />
        ) : (
          <div className="space-y-8">
            {/* Accounts Overview */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Accounts</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {accounts.map((account) => (
                  <Card key={account.id}>
                    <CardHeader>
                      <CardTitle className="text-sm font-medium text-gray-600">
                        {formatAccountNumber(account.account_number)}
                      </CardTitle>
                      <CardDescription className="flex items-center justify-between">
                        <span>{account.account_type}</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getAccountStatusColor(account.status)}`}>
                          {account.status}
                        </span>
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-gray-900">
                        {formatCurrency(account.balance, account.currency)}
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        Available balance
                      </p>
                    </CardContent>
                  </Card>
                ))}
                
                {accounts.length === 0 && (
                  <Card className="col-span-full">
                    <CardContent className="text-center py-8">
                      <EmptyState
                        icon="💳"
                        title="No accounts found"
                        description="You don't have any accounts yet. Create your first account to get started."
                        action={{
                          label: "Create Account",
                          onClick: () => router.push('/accounts/create')
                        }}
                      />
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>

            {/* Recent Transactions */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Recent Transactions</h3>
                <Button variant="outline" size="sm">
                  View All
                </Button>
              </div>
              
              <Card>
                <CardContent className="p-0">
                  {transactions.length > 0 ? (
                    <div className="divide-y">
                      {transactions.map((transaction) => (
                        <div key={transaction.id} className="p-4 hover:bg-gray-50">
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium text-gray-900">
                                {transaction.description || 'Transfer'}
                              </p>
                              <p className="text-sm text-gray-500">
                                From: {formatAccountNumber(transaction.from_account)} → To: {formatAccountNumber(transaction.to_account)}
                              </p>
                              <p className="text-xs text-gray-400 mt-1">
                                {formatDate(transaction.created_at)}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="font-semibold text-gray-900">
                                {formatCurrency(transaction.amount, transaction.currency)}
                              </p>
                              <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium mt-1 ${getTransactionStatusColor(transaction.status)}`}>
                                {transaction.status}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <EmptyState
                      icon="📋"
                      title="No transactions yet"
                      description="Start by making your first transfer or check back later for new transactions."
                      action={{
                        label: "Make Transfer",
                        onClick: () => router.push('/transfer')
                      }}
                    />
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Link href="/transfer">
                  <Card className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="text-center py-6">
                      <div className="text-2xl mb-2">💸</div>
                      <h4 className="font-medium text-gray-900">Send Money</h4>
                      <p className="text-sm text-gray-500 mt-1">Transfer funds to another account</p>
                    </CardContent>
                  </Card>
                </Link>
                
                <Link href="/history">
                  <Card className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="text-center py-6">
                      <div className="text-2xl mb-2">📊</div>
                      <h4 className="font-medium text-gray-900">View History</h4>
                      <p className="text-sm text-gray-500 mt-1">See all your transactions</p>
                    </CardContent>
                  </Card>
                </Link>
                
                <Card className="cursor-pointer hover:shadow-md transition-shadow">
                  <CardContent className="text-center py-6">
                    <div className="text-2xl mb-2">⚙️</div>
                    <h4 className="font-medium text-gray-900">Settings</h4>
                    <p className="text-sm text-gray-500 mt-1">Manage your account settings</p>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
