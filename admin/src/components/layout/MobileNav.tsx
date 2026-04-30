'use client';

import { cn } from '@/lib/utils';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Phone, Calendar, Settings } from 'lucide-react';

const items = [
  { label: 'Дашборд', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Звонки', href: '/calls', icon: Phone },
  { label: 'Записи', href: '/bookings', icon: Calendar },
  { label: 'Настройки', href: '/settings', icon: Settings },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-30 bg-card border-t border-border safe-area-bottom">
      <div className="flex items-center justify-around h-14">
        {items.map(item => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex flex-col items-center justify-center gap-0.5 px-3 py-1 min-w-[60px]',
                'transition-colors duration-150',
                isActive ? 'text-primary-500' : 'text-text-tertiary'
              )}
            >
              <Icon size={20} />
              <span className="text-[10px] font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
