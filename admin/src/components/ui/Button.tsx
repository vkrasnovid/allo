'use client';

import { cn } from '@/lib/utils';
import { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'lg' | 'md' | 'sm';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: ReactNode;
  loading?: boolean;
  fullWidth?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-primary-500 text-white hover:bg-primary-600 active:bg-primary-700 disabled:opacity-40',
  secondary: 'bg-card border border-primary-500 text-primary-500 hover:bg-primary-50 disabled:opacity-40',
  ghost: 'bg-transparent text-text-primary hover:bg-gray-100 disabled:opacity-40',
  danger: 'bg-error text-white hover:bg-red-600 active:bg-red-700 disabled:opacity-40',
};

const sizeStyles: Record<ButtonSize, string> = {
  lg: 'h-12 px-4 md:px-6 text-base font-semibold',
  md: 'h-10 px-3 md:px-5 text-base font-semibold',
  sm: 'h-8 px-2 md:px-3 text-sm font-semibold',
};

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  loading,
  fullWidth,
  className,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-md transition-colors duration-150',
        'focus-visible:outline-2 focus-visible:outline-primary-500 focus-visible:outline-offset-2',
        'min-touch-target',
        variantStyles[variant],
        sizeStyles[size],
        fullWidth && 'w-full',
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {children}
        </span>
      ) : children}
    </button>
  );
}
