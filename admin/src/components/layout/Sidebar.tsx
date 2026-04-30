'use client';

import { cn } from '@/lib/utils';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Phone, Calendar, Settings } from 'lucide-react';

const navItems = [
  { label: 'Дашборд', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Звонки', href: '/calls', icon: Phone },
  { label: 'Записи', href: '/bookings', icon: Calendar },
  { label: 'Настройки', href: '/settings', icon: Settings },
];

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div className="fixed inset-0 bg-black/40 z-40 md:hidden" onClick={onClose} />
      )}

      <aside className={cn(
        'fixed md:static inset-y-0 left-0 z-50 w-60 bg-card border-r border-border',
        'flex flex-col transition-transform duration-300 ease-in-out',
        'md:translate-x-0',
        open ? 'translate-x-0' : '-translate-x-full'
      )}>
        {/* Logo */}
        <div className="flex items-center gap-2 px-5 py-4 border-b border-border">
          <div className="w-8 h-8 rounded-lg bg-primary-500 flex items-center justify-center text-white font-bold text-sm">
            А
          </div>
          <span className="text-lg font-bold text-text-primary">Алло</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-3">
          {navItems.map(item => {
            const isActive = pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  'flex items-center gap-3 px-5 py-3 text-sm font-medium transition-colors',
                  'border-l-[3px] border-transparent',
                  isActive
                    ? 'bg-primary-100 text-primary-500 border-l-primary-500'
                    : 'text-text-secondary hover:bg-gray-50 hover:text-text-primary'
                )}
              >
                <Icon size={20} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Status */}
        <div className="border-t border-border p-4">
          <div className="flex items-center gap-2 text-sm text-text-secondary">
            <span className="w-2 h-2 rounded-full bg-success" />
            <span>Алло активен</span>
          </div>
        </div>
      </aside>
    </>
  );
}
