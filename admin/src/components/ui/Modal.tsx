'use client';

import { cn } from '@/lib/utils';
import { useEffect, useRef, ReactNode } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
  className?: string;
}

export function Modal({ open, onClose, children, title, className }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

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
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={(e) => e.target === overlayRef.current && onClose()}
    >
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" />
      <div className={cn(
        'relative bg-card rounded-lg shadow-modal w-full max-w-lg z-10',
        'animate-[fadeIn_200ms_ease-out,slideUp_200ms_ease-out]',
        className
      )}>
        {title && (
          <div className="flex items-center justify-between px-5 pt-5 pb-3 border-b border-border">
            <h2 className="text-xl font-semibold text-text-primary">{title}</h2>
            <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-md transition-colors">
              <X size={20} className="text-text-secondary" />
            </button>
          </div>
        )}
        <div className="p-5">{children}</div>
      </div>
      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from { transform: scale(0.95) translateY(10px); opacity: 0; }
          to { transform: scale(1) translateY(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
