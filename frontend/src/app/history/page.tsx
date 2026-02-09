'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient, Transaction } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingState } from '@/components/ui/LoadingState';
import { EmptyState } from '@/components/ui/EmptyState';
import { Navigation } from '@/components/layout/Navigation';
import { formatCurrency, formatDate, formatAccountNumber, getTransactionStatusColor } from '@/lib/utils';
import Link from 'next/link';

export default function HistoryPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoadingTransactions, setIsLoadingTransactions] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Redirect if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [isLoading, isAuthenticated, router]);

  // Load transactions when authenticated or filters change
  useEffect(() => {
    if (isAuthenticated) {
      loadTransactions();
    }
  }, [isAuthenticated, currentPage, statusFilter]);

  const loadTransactions = async () => {
    try {
      setIsLoadingTransactions(true);
      const params: any = {
        page: currentPage,
        page_size: 10,
      };

      if (statusFilter) {
        params.status = statusFilter;
      }

      const response = await apiClient.getTransactions(params);
      setTransactions(response.results);
      setTotalCount(response.count);
    } catch (error) {
      console.error('Failed to load transactions:', error);
    } finally {
      setIsLoadingTransactions(false);
    }
  };

  const filteredTransactions = transactions.filter(transaction => {
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    return (
      transaction.description?.toLowerCase().includes(searchLower) ||
      transaction.from_account.toLowerCase().includes(searchLower) ||
      transaction.to_account.toLowerCase().includes(searchLower) ||
      transaction.amount.toLowerCase().includes(searchLower) ||
      transaction.status.toLowerCase().includes(searchLower)
    );
  });

  const totalPages = Math.ceil(totalCount / 10);

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
      <Navigation currentPage="history" />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Transaction History</h2>
          <p className="text-gray-600">View and search all your transactions</p>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
                  Search
                </label>
                <Input
                  id="search"
                  type="text"
                  placeholder="Search transactions..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              
              <div>
                <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  id="status"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full h-10 rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                >
                  <option value="">All Statuses</option>
                  <option value="COMPLETED">Completed</option>
                  <option value="PENDING">Pending</option>
                  <option value="FAILED">Failed</option>
                  <option value="CANCELLED">Cancelled</option>
                </select>
              </div>

              <div className="flex items-end">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setSearchTerm('');
                    setStatusFilter('');
                    setCurrentPage(1);
                  }}
                  className="w-full"
                >
                  Clear Filters
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Transactions List */}
        <Card>
          <CardHeader>
            <CardTitle>Transactions</CardTitle>
            <CardDescription>
              {totalCount > 0 ? `${totalCount} total transactions` : 'No transactions found'}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {isLoadingTransactions ? (
              <LoadingState message="Loading transactions..." />
            ) : filteredTransactions.length > 0 ? (
              <>
                <div className="divide-y">
                  {filteredTransactions.map((transaction) => (
                    <div key={transaction.id} className="p-4 hover:bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <p className="font-medium text-gray-900">
                              {transaction.description || 'Transfer'}
                            </p>
                            <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getTransactionStatusColor(transaction.status)}`}>
                              {transaction.status}
                            </span>
                          </div>
                          <div className="text-sm text-gray-500 space-y-1">
                            <p>
                              From: <span className="font-mono">{formatAccountNumber(transaction.from_account)}</span> → 
                              To: <span className="font-mono">{formatAccountNumber(transaction.to_account)}</span>
                            </p>
                            <p>{formatDate(transaction.created_at)}</p>
                          </div>
                        </div>
                        <div className="text-right ml-4">
                          <p className="font-semibold text-gray-900">
                            {formatCurrency(transaction.amount, transaction.currency)}
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            {transaction.currency}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="p-4 border-t">
                    <div className="flex justify-between items-center">
                      <Button
                        variant="outline"
                        onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                        disabled={currentPage === 1}
                      >
                        Previous
                      </Button>
                      
                      <span className="text-sm text-gray-600">
                        Page {currentPage} of {totalPages}
                      </span>
                      
                      <Button
                        variant="outline"
                        onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                        disabled={currentPage === totalPages}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <EmptyState
                icon="📋"
                title={searchTerm || statusFilter ? 'No transactions match your filters' : 'No transactions found'}
                description={searchTerm || statusFilter ? 'Try adjusting your search criteria' : 'Start by making your first transfer or check back later for new transactions.'}
                action={{
                  label: "Make Your First Transfer",
                  onClick: () => router.push('/transfer')
                }}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
