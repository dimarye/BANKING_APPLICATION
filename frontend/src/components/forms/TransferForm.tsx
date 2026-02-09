'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { apiClient, BankAccount } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';

const transferSchema = z.object({
  from_account: z.string().min(1, 'Please select a source account'),
  to_account: z.string().min(1, 'Recipient account number is required').regex(/^\d+$/, 'Account number must contain only digits'),
  amount: z.string().min(1, 'Amount is required').regex(/^\d+(\.\d{1,2})?$/, 'Invalid amount format'),
  currency: z.string().min(1, 'Currency is required'),
  description: z.string().optional(),
});

type TransferFormData = z.infer<typeof transferSchema>;

interface TransferFormProps {
  accounts: BankAccount[];
  onSuccess?: () => void;
}

export function TransferForm({ accounts, onSuccess }: TransferFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
  } = useForm<TransferFormData>({
    resolver: zodResolver(transferSchema),
  });

  const selectedFromAccount = watch('from_account');
  const selectedCurrency = watch('currency');

  // Set currency when from account changes
  React.useEffect(() => {
    if (selectedFromAccount) {
      const account = accounts.find(acc => acc.id.toString() === selectedFromAccount);
      if (account) {
        setValue('currency', account.currency);
      }
    }
  }, [selectedFromAccount, accounts, setValue]);

  const onSubmit = async (data: TransferFormData) => {
    setIsSubmitting(true);
    setError('');
    setSuccess('');

    try {
      // Convert amount to number for validation
      const amount = parseFloat(data.amount);
      
      // Check if source account has sufficient funds
      const sourceAccount = accounts.find(acc => acc.id.toString() === data.from_account);
      if (sourceAccount && parseFloat(sourceAccount.balance) < amount) {
        setError('Insufficient funds in source account');
        return;
      }

      // Prevent transfer to same account
      if (data.from_account === data.to_account) {
        setError('Cannot transfer to the same account');
        return;
      }

      await apiClient.createTransfer({
        from_account: data.from_account,
        to_account: data.to_account,
        amount: data.amount,
        currency: data.currency,
        description: data.description,
      });

      setSuccess('Transfer completed successfully!');
      onSuccess?.();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Transfer failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const sourceAccount = accounts.find(acc => acc.id.toString() === selectedFromAccount);
  const availableBalance = sourceAccount ? parseFloat(sourceAccount.balance) : 0;

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Make a Transfer</CardTitle>
        <CardDescription>
          Send money to another account instantly
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Source Account */}
          <div>
            <label htmlFor="from_account" className="block text-sm font-medium text-gray-700 mb-1">
              From Account
            </label>
            <select
              id="from_account"
              {...register('from_account')}
              className="w-full h-10 rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              disabled={isSubmitting}
            >
              <option value="">Select an account</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.account_number} - {formatCurrency(account.balance, account.currency)} ({account.account_type})
                </option>
              ))}
            </select>
            {errors.from_account && (
              <p className="mt-1 text-sm text-red-600">{errors.from_account.message}</p>
            )}
          </div>

          {/* Recipient Account */}
          <div>
            <label htmlFor="to_account" className="block text-sm font-medium text-gray-700 mb-1">
              To Account Number
            </label>
            <Input
              id="to_account"
              type="text"
              placeholder="Enter recipient account number"
              {...register('to_account')}
              disabled={isSubmitting}
            />
            {errors.to_account && (
              <p className="mt-1 text-sm text-red-600">{errors.to_account.message}</p>
            )}
          </div>

          {/* Amount */}
          <div>
            <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-1">
              Amount
            </label>
            <div className="relative">
              <Input
                id="amount"
                type="number"
                step="0.01"
                placeholder="0.00"
                {...register('amount')}
                disabled={isSubmitting}
                className="pl-12"
              />
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="text-gray-500 sm:text-sm">{selectedCurrency || 'USD'}</span>
              </div>
            </div>
            {errors.amount && (
              <p className="mt-1 text-sm text-red-600">{errors.amount.message}</p>
            )}
            {sourceAccount && (
              <p className="mt-1 text-sm text-gray-500">
                Available balance: {formatCurrency(sourceAccount.balance, sourceAccount.currency)}
              </p>
            )}
          </div>

          {/* Currency (hidden, set automatically) */}
          <input type="hidden" {...register('currency')} />

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description (Optional)
            </label>
            <Input
              id="description"
              type="text"
              placeholder="What's this transfer for?"
              {...register('description')}
              disabled={isSubmitting}
            />
            {errors.description && (
              <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
            )}
          </div>

          {/* Error/Success Messages */}
          {error && (
            <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          {success && (
            <div className="p-3 bg-green-100 border border-green-400 text-green-700 rounded">
              {success}
            </div>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            disabled={isSubmitting || accounts.length === 0}
          >
            {isSubmitting ? 'Processing Transfer...' : 'Send Money'}
          </Button>

          {accounts.length === 0 && (
            <p className="text-center text-sm text-gray-500">
              You need at least one account to make transfers
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
