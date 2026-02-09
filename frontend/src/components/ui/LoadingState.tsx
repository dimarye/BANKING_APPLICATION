import React from 'react';
import { Spinner } from './Spinner';

interface LoadingStateProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function LoadingState({ message = 'Loading...', size = 'md' }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <Spinner size={size} />
      <p className="mt-4 text-gray-600">{message}</p>
    </div>
  );
}
