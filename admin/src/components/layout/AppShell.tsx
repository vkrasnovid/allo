'use client';

import { useState, ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { MobileNav } from './MobileNav';

const pageTitles: Record<string, string> = {
  '/dashboard': 'Дашборд',
  '/calls': 'Звонки',
  '/bookings': 'Записи',
  '/settings': 'Настройки',
};

interface AppShellProps {
  children: ReactNode;
  hideNavigation?: boolean;
  pageTitle?: string;
}

export function AppShell({ children, hideNavigation, pageTitle }: AppShellProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();

  const title = pageTitle || pageTitles[pathname] || 'Алло';

  if (hideNavigation) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-surface">
      <Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} />
      
      <div className="md:ml-60 flex flex-col min-h-screen pb-14 md:pb-0">
        <TopBar title={title} menuOpen={menuOpen} onMenuToggle={() => setMenuOpen(prev => !prev)} />
        
        <main className="flex-1 px-4 py-5 md:px-6 md:py-6 max-w-5xl mx-auto w-full">
          {children}
        </main>
      </div>

      <MobileNav />
    </div>
  );
}
