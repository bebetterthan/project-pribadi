import React from 'react';
import { cn } from '@/lib/utils';
import { STATUS_COLORS, STATUS_LABELS } from '@/lib/constants';

interface BadgeProps {
  status?: 'pending' | 'running' | 'completed' | 'failed';
  className?: string;
  children?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ status, className, children }) => {
  const statusColors: Record<string, string> = STATUS_COLORS;
  const statusLabels: Record<string, string> = STATUS_LABELS;

  // If children provided, use that (custom badge)
  if (children) {
    return (
      <span
        className={cn(
          'px-2 py-1 text-xs font-semibold rounded-full',
          className
        )}
      >
        {children}
      </span>
    );
  }

  // Otherwise use status badge (original behavior)
  return (
    <span
      className={cn(
        'px-2 py-1 text-xs font-semibold rounded-full text-white',
        status ? statusColors[status] : '',
        className
      )}
    >
      {status ? statusLabels[status] : ''}
    </span>
  );
};
