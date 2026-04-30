'use client';

import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { ExternalLink } from 'lucide-react';
import { cn, formatPhone, formatTime, formatDuration, getResultBadgeVariant } from '@/lib/utils';
import { CALL_STATUS_LABELS } from '@/lib/types';
import type { Call } from '@/lib/types';

interface CallTableProps {
  calls: Call[];
  loading?: boolean;
  onSelect: (call: Call) => void;
}

export function CallTable({ calls, loading, onSelect }: CallTableProps) {
  if (loading) {
    return (
      <div className="hidden md:block bg-card rounded-md border border-border">
        <div className="divide-y divide-border">
          {[1,2,3].map(i => (
            <div key={i} className="p-4 flex gap-4">
              <Skeleton width={60} height={16} />
              <Skeleton width={80} height={16} />
              <Skeleton width={120} height={16} />
              <Skeleton width={80} height={16} />
              <Skeleton width={36} height={16} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="hidden md:block bg-card rounded-md border border-border overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-border bg-gray-50/50">
            <th className="text-left text-xs font-medium text-text-tertiary px-4 py-3">Время</th>
            <th className="text-left text-xs font-medium text-text-tertiary px-4 py-3">Номер</th>
            <th className="text-left text-xs font-medium text-text-tertiary px-4 py-3">Клиент</th>
            <th className="text-left text-xs font-medium text-text-tertiary px-4 py-3">Результат</th>
            <th className="text-right text-xs font-medium text-text-tertiary px-4 py-3">Длит.</th>
            <th className="w-10 px-4 py-3"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {calls.map((call, i) => (
            <tr
              key={call.id}
              onClick={() => onSelect(call)}
              className={cn(
                'cursor-pointer transition-colors hover:bg-primary-50',
                i % 2 === 1 ? 'bg-surface/50' : 'bg-card'
              )}
            >
              <td className="px-4 py-3 text-sm text-text-secondary">{formatTime(call.created_at)}</td>
              <td className="px-4 py-3 text-sm text-text-primary font-medium">{formatPhone(call.caller_phone)}</td>
              <td className="px-4 py-3 text-sm text-text-primary">{call.client_name || '—'}</td>
              <td className="px-4 py-3">
                <Badge variant={getResultBadgeVariant(call.result) as 'success' | 'warning' | 'error' | 'neutral'}>
                  {CALL_STATUS_LABELS[call.result] || call.result}
                </Badge>
              </td>
              <td className="px-4 py-3 text-sm text-text-secondary text-right">{formatDuration(call.duration_sec || 0)}</td>
              <td className="px-4 py-3">
                <ExternalLink size={14} className="text-text-tertiary" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
