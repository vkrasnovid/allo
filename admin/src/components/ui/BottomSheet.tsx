'use client';

import { cn } from '@/lib/utils';
import { useEffect, ReactNode } from 'react';
import { X } from 'lucide-react';

interface BottomSheetProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
  className?: string;
}

export function BottomSheet({ open, onClose, children, title, className }: BottomSheetProps) {
  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50" onClick={onClose} />
      <div className={cn(
        'fixed bottom-0 left-0 right-0 z-50 bg-card rounded-t-xl shadow-modal',
        'max-h-[85vh] overflow-y-auto',
        'animate-[slideUp_300ms_cubic-bezier(0.32,0.72,0,1)]',
        'md:max-w-lg md:left-1/2 md:-translate-x-1/2 md:rounded-xl md:bottom-auto md:top-1/2 md:-translate-y-1/2 md:max-h-[80vh]',
        className
      )}>
        {/* Drag handle (mobile) */}
        <div className="flex justify-center pt-2 pb-1 md:hidden">
          <div className="w-9 h-1 rounded-full bg-border" />
        </div>

        {/* Header */}
        {title && (
          <div className="flex items-center justify-between px-4 py-3 border-b border-border">
            <h2 className="text-lg font-semibold text-text-primary">{title}</h2>
            <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-md transition-colors">
              <X size={20} className="text-text-secondary" />
            </button>
          </div>
        )}

        <div className="p-4">{children}</div>
      </div>
      <style jsx>{`
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
        @media (min-width: 768px) {
          @keyframes slideUp {
            from { transform: translate(-50%, -50%) scale(0.95); opacity: 0; }
            to { transform: translate(-50%, -50%) scale(1); opacity: 1; }
          }
        }
      `}</style>
    </>
  );
}
