'use client';

import { cn } from '@/lib/utils';
import { InputHTMLAttributes, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, helperText, error, className, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-text-primary">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'h-11 md:h-10 px-3 rounded-sm border text-base md:text-sm',
            'bg-card text-text-primary placeholder:text-text-tertiary',
            'border-border focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20',
            'transition-colors duration-150 outline-none',
            error && 'border-error focus:border-error focus:ring-error/20',
            className
          )}
          {...props}
        />
        {error && <p className="text-xs text-error mt-0.5">{error}</p>}
        {helperText && !error && <p className="text-xs text-text-tertiary mt-0.5">{helperText}</p>}
      </div>
    );
  }
);
Input.displayName = 'Input';

interface TextareaProps {
  label?: string;
  helperText?: string;
  error?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  placeholder?: string;
  rows?: number;
  className?: string;
}

export function Textarea({ label, helperText, error, className, ...props }: TextareaProps) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && <label className="text-sm font-medium text-text-primary">{label}</label>}
      <textarea
        className={cn(
          'px-3 py-2 rounded-sm border text-base md:text-sm',
          'bg-card text-text-primary placeholder:text-text-tertiary',
          'border-border focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20',
          'transition-colors duration-150 outline-none resize-vertical',
          'min-h-[80px]',
          error && 'border-error',
          className
        )}
        {...props}
      />
      {error && <p className="text-xs text-error mt-0.5">{error}</p>}
      {helperText && !error && <p className="text-xs text-text-tertiary mt-0.5">{helperText}</p>}
    </div>
  );
}
