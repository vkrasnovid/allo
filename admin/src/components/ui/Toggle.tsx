'use client';

import { cn } from '@/lib/utils';

interface ToggleProps {
  label: string;
  enabled: boolean;
  onChange: (enabled: boolean) => void;
  description?: string;
  disabled?: boolean;
}

export function Toggle({ label, enabled, onChange, description, disabled }: ToggleProps) {
  return (
    <label className={cn(
      'flex items-center justify-between py-3 px-0 cursor-pointer',
      disabled && 'opacity-50 cursor-not-allowed'
    )}>
      <div className="flex flex-col gap-0.5">
        <span className="text-sm font-medium text-text-primary">{label}</span>
        {description && <span className="text-xs text-text-tertiary">{description}</span>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={enabled}
        disabled={disabled}
        onClick={() => onChange(!enabled)}
        className={cn(
          'relative inline-flex h-6 w-11 shrink-0 rounded-full border-2 border-transparent',
          'transition-colors duration-200 ease-in-out',
          'focus-visible:outline-2 focus-visible:outline-primary-500 focus-visible:outline-offset-2',
          enabled ? 'bg-primary-500' : 'bg-gray-200'
        )}
      >
        <span
          className={cn(
            'pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-md',
            'transform transition-transform duration-200 ease-in-out',
            enabled ? 'translate-x-5' : 'translate-x-0'
          )}
        />
      </button>
    </label>
  );
}
