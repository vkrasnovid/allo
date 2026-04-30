'use client';

import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  trend?: string;
  trendUp?: boolean;
  loading?: boolean;
}

export function StatCard({ label, value, icon, trend, trendUp, loading }: StatCardProps) {
  if (loading) {
    return (
      <div className="bg-card border border-border rounded-md p-4">
        <div className="skeleton-shimmer h-3 w-20 rounded mb-2" />
        <div className="skeleton-shimmer h-9 w-16 rounded mb-1" />
        <div className="skeleton-shimmer h-3 w-12 rounded" />
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-md p-4 transition-colors hover:border-primary-200">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-text-secondary">{label}</span>
        <span className="text-primary-400">{icon}</span>
      </div>
      <div className="text-[36px] font-bold text-text-primary leading-none mb-1">{value}</div>
      {trend && (
        <span className={cn(
          'text-xs font-medium',
          trendUp ? 'text-success' : 'text-text-tertiary'
        )}>
          {trend}
        </span>
      )}
    </div>
  );
}
