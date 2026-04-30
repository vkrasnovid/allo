'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { SkeletonText } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ArrowRight, CalendarX } from 'lucide-react';
import { cn, formatDate, formatTime, formatPrice, getStatusBgColor } from '@/lib/utils';
import type { Booking } from '@/lib/types';
import Link from 'next/link';

interface UpcomingBookingsListProps {
  bookings: Booking[];
  loading?: boolean;
}

export function UpcomingBookingsList({ bookings, loading }: UpcomingBookingsListProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Ближайшие записи</CardTitle></CardHeader>
        <CardContent>
          <div className="flex flex-col gap-3">
            {[1,2].map(i => <SkeletonText key={i} lines={2} />)}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Ближайшие записи</CardTitle>
        <Link href="/bookings" className="text-sm text-primary-500 hover:text-primary-700 font-medium flex items-center gap-1">
          Все <ArrowRight size={14} />
        </Link>
      </CardHeader>
      <CardContent>
        {bookings.length === 0 ? (
          <EmptyState
            icon={<CalendarX size={48} />}
            title="Записей пока нет"
            description="Клиенты ещё не записались через Алло."
          />
        ) : (
          <div className="flex flex-col divide-y divide-border">
            {bookings.slice(0, 5).map(booking => (
              <Link
                key={booking.id}
                href="/bookings"
                className="py-3 flex items-start gap-3 hover:bg-primary-50 -mx-4 px-4 rounded-sm transition-colors"
              >
                <span className="text-lg mt-0.5">✂️</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-medium text-text-primary">{booking.client_name}</span>
                    <span className={cn('text-xs font-medium px-1.5 py-0.5 rounded', getStatusBgColor(booking.status))}>
                      {booking.status === 'confirmed' ? 'Подтверждена' :
                       booking.status === 'pending' ? 'Ожидает' :
                       booking.status === 'cancelled' ? 'Отменена' : 'Выполнена'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-text-tertiary">
                    <span>{booking.service_name}</span>
                    <span>·</span>
                    <span>{booking.master_name}</span>
                  </div>
                  <div className="text-xs text-text-secondary mt-0.5">
                    {formatDate(booking.start_at)}, {formatTime(booking.start_at)} · {formatPrice(booking.price_rub)}
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
