import React from 'react';
import { cn } from '@/lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ children, className, ...props }) => {
  return (
    <div className={cn('bg-[#2f2f2f] border border-[#565656] rounded-xl shadow-lg p-6', className)} {...props}>
      {children}
    </div>
  );
};
