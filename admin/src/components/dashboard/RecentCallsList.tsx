'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { SkeletonText } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { Badge } from '@/components/ui/Badge';
import { Phone, PhoneOff, ArrowRight } from 'lucide-react';
import { formatPhone, formatTime, getResultBadgeVariant } from '@/lib/utils';
import { CALL_STATUS_LABELS } from '@/lib/types';
import type { Call } from '@/lib/types';
import Link from 'next/link';

interface RecentCallsListProps {
  calls: Call[];
  loading?: boolean;
}

export function RecentCallsList({ calls, loading }: RecentCallsListProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Последние звонки</CardTitle></CardHeader>
        <CardContent>
          <div className="flex flex-col gap-3">
            {[1,2,3].map(i => <SkeletonText key={i} lines={2} />)}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Последние звонки</CardTitle>
        <Link href="/calls" className="text-sm text-primary-500 hover:text-primary-700 font-medium flex items-center gap-1">
          Все <ArrowRight size={14} />
        </Link>
      </CardHeader>
      <CardContent>
        {calls.length === 0 ? (
          <EmptyState
            icon={<PhoneOff size={48} />}
            title="Звонков пока нет"
            description="Алло ещё не принимал звонки на этот номер."
            action={{ label: 'Проверить настройки', onClick: () => window.location.href = '/settings' }}
          />
        ) : (
          <div className="flex flex-col divide-y divide-border">
            {calls.slice(0, 5).map(call => (
              <Link
                key={call.id}
                href={`/calls/${call.id}`}
                className="py-3 flex items-start gap-3 hover:bg-primary-50 -mx-4 px-4 rounded-sm transition-colors"
              >
                <Phone size={16} className="text-primary-400 mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-medium text-text-primary">
                      {call.client_name || formatPhone(call.caller_phone)}
                    </span>
                    <Badge variant={getResultBadgeVariant(call.result) as 'success' | 'warning' | 'error' | 'neutral'}>
                      {CALL_STATUS_LABELS[call.result] || call.result}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-text-tertiary">
                    <span>{formatPhone(call.caller_phone)}</span>
                    <span>·</span>
                    <span>{formatTime(call.created_at)}</span>
                    {call.duration_sec && (
                      <>
                        <span>·</span>
                        <span>{Math.floor(call.duration_sec / 60)} мин</span>
                      </>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
