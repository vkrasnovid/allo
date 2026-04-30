'use client';

import { cn } from '@/lib/utils';
import type { BadgeVariant } from '@/lib/types';

interface BadgeProps {
  children: React.ReactNode;
  variant: BadgeVariant;
  className?: string;
}

const styles: Record<BadgeVariant, string> = {
  success: 'bg-success-bg text-success-text',
  warning: 'bg-warning-bg text-warning-text',
  error: 'bg-error-bg text-error-text',
  neutral: 'bg-gray-100 text-gray-600',
  primary: 'bg-primary-100 text-primary-700',
};

export function Badge({ children, variant, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-pill text-xs font-medium',
        styles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

interface StatusDotProps {
  status: 'active' | 'inactive';
  className?: string;
}

export function StatusDot({ status, className }: StatusDotProps) {
  return (
    <span className={cn(
      'inline-block w-2 h-2 rounded-full',
      status === 'active' ? 'bg-success' : 'bg-gray-300',
      className
    )} />
  );
}
