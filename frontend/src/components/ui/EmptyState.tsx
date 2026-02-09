import React from 'react';
import { Button } from './Button';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  icon?: string;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'default' | 'outline' | 'secondary';
  };
  className?: string;
}

export function EmptyState({ 
  icon = '📭', 
  title, 
  description, 
  action, 
  className 
}: EmptyStateProps) {
  return (
    <div className={cn('text-center py-12', className)}>
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500 mb-6">{description}</p>
      {action && (
        <Button 
          variant={action.variant || 'default'} 
          onClick={action.onClick}
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}
