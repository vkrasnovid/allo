'use client';

import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  rounded?: boolean;
}

export function Skeleton({ className, width, height, rounded }: SkeletonProps) {
  return (
    <div
      className={cn(
        'skeleton-shimmer',
        rounded ? 'rounded-full' : 'rounded-md',
        className
      )}
      style={{ width, height }}
    />
  );
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('bg-card rounded-md p-4 border border-border', className)}>
      <Skeleton width="60%" height={20} className="mb-3" />
      <Skeleton width="40%" height={14} className="mb-2" />
      <Skeleton width="80%" height={14} />
    </div>
  );
}

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="flex flex-col gap-2">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} width={`${80 - i * 15}%`} height={14} />
      ))}
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="bg-card rounded-md p-4 border border-border">
      <Skeleton width="50%" height={14} className="mb-2" />
      <Skeleton width="64px" height={36} className="mb-1" />
    </div>
  );
}
