'use client';

import { Menu, X } from 'lucide-react';

interface TopBarProps {
  title: string;
  menuOpen: boolean;
  onMenuToggle: () => void;
  salonName?: string;
}

export function TopBar({ title, menuOpen, onMenuToggle, salonName = 'Студия красоты "Элегия"' }: TopBarProps) {
  return (
    <header className="sticky top-0 z-30 bg-card border-b border-border h-14 md:h-16">
      <div className="flex items-center justify-between h-full px-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuToggle}
            className="md:hidden p-2 -ml-2 rounded-md hover:bg-gray-100 transition-colors min-touch-target"
            aria-label={menuOpen ? 'Закрыть меню' : 'Открыть меню'}
          >
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
          <h1 className="text-lg font-semibold text-text-primary md:hidden">{title}</h1>
          {/* Desktop left */}
          <div className="hidden md:flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-primary-500 flex items-center justify-center text-white font-bold text-xs">
              А
            </div>
            <span className="text-sm font-semibold text-text-primary">{title}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-text-secondary hidden md:block">{salonName}</span>
          <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-semibold">
            В
          </div>
        </div>
      </div>
    </header>
  );
}
