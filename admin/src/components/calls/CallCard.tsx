'use client';

import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Phone } from 'lucide-react';
import { formatPhone, formatTime, formatDuration, getResultBadgeVariant } from '@/lib/utils';
import { CALL_STATUS_LABELS } from '@/lib/types';
import type { Call } from '@/lib/types';

interface CallCardProps {
  call: Call;
  loading?: boolean;
  onClick: () => void;
}

export function CallCard({ call, loading, onClick }: CallCardProps) {
  if (loading) {
    return (
      <div className="bg-card rounded-md border border-border p-4 md:hidden">
        <Skeleton width={140} height={16} className="mb-2" />
        <Skeleton width={100} height={14} className="mb-2" />
        <Skeleton width={80} height={14} />
      </div>
    );
  }

  return (
    <div
      onClick={onClick}
      className="md:hidden bg-card rounded-md border border-border p-4 cursor-pointer hover:shadow-md transition-all duration-200 active:scale-[0.99]"
    >
      <div className="flex items-start gap-3">
        <Phone size={16} className="text-primary-400 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-text-primary text-sm">
              {call.client_name || formatPhone(call.caller_phone)}
            </span>
            <Badge variant={getResultBadgeVariant(call.result) as 'success' | 'warning' | 'error' | 'neutral'}>
              {CALL_STATUS_LABELS[call.result] || call.result}
            </Badge>
          </div>
          <p className="text-xs text-text-tertiary mb-1">{formatPhone(call.caller_phone)}</p>
          <div className="flex items-center gap-2 text-xs text-text-secondary">
            <span>{formatTime(call.created_at)}</span>
            <span>·</span>
            <span>{formatDuration(call.duration_sec || 0)}</span>
          </div>
          {call.transcript && call.transcript.length > 0 && (
            <p className="text-xs text-text-tertiary mt-2 line-clamp-2">
              {call.transcript.map(t => t.text).join(' ')}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
