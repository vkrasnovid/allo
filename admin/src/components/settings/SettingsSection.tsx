'use client';

import { useState, ReactNode } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SettingsSectionProps {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
}

export function SettingsSection({ title, children, defaultOpen = true }: SettingsSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="bg-card border border-border rounded-md overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3.5 hover:bg-gray-50 transition-colors"
      >
        <h3 className="font-semibold text-text-primary text-sm">{title}</h3>
        <ChevronDown
          size={18}
          className={cn(
            'text-text-tertiary transition-transform duration-200',
            open && 'rotate-180'
          )}
        />
      </button>
      <div className={cn(
        'overflow-hidden transition-all duration-200',
        open ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
      )}>
        <div className="px-4 pb-4 border-t border-border pt-3">
          {children}
        </div>
      </div>
    </div>
  );
}
