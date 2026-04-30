'use client';

import { formatDate, formatTime, formatPrice, cn, getStatusBgColor } from '@/lib/utils';
import { Skeleton } from '@/components/ui/Skeleton';
import { Edit2, X } from 'lucide-react';
import type { Booking } from '@/lib/types';

interface BookingCardProps {
  booking: Booking;
  loading?: boolean;
  onCancel?: (id: string) => void;
}

export function BookingCard({ booking, loading, onCancel }: BookingCardProps) {
  if (loading) {
    return (
      <div className="bg-card rounded-md border border-border p-4">
        <Skeleton width="60%" height={16} className="mb-2" />
        <Skeleton width="80%" height={14} className="mb-1" />
        <Skeleton width="40%" height={14} />
      </div>
    );
  }

  return (
    <div className="group bg-card rounded-md border border-border p-4 hover:shadow-md transition-all">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">✂️</span>
          <div>
            <span className="font-medium text-text-primary text-sm">{booking.client_name}</span>
            <span className={cn('ml-2 text-xs px-1.5 py-0.5 rounded font-medium', getStatusBgColor(booking.status))}>
              {booking.status === 'confirmed' ? 'Подтверждена' :
               booking.status === 'pending' ? 'Ожидает' :
               booking.status === 'cancelled' ? 'Отменена' : 'Выполнена'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button className="p-1.5 text-text-tertiary hover:text-text-primary rounded-md hover:bg-gray-100">
            <Edit2 size={14} />
          </button>
          {onCancel && booking.status !== 'cancelled' && booking.status !== 'completed' && (
            <button
              onClick={() => onCancel(booking.id)}
              className="p-1.5 text-text-tertiary hover:text-error rounded-md hover:bg-error-bg"
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      <div className="ml-7">
        <p className="text-sm text-text-secondary">{booking.service_name}</p>
        <p className="text-xs text-text-tertiary">Мастер: {booking.master_name}</p>
        <div className="flex items-center gap-2 mt-1 text-xs text-text-secondary">
          <span>{formatDate(booking.start_at)}, {formatTime(booking.start_at)}</span>
          <span>·</span>
          <span>{formatPrice(booking.price_rub)}</span>
        </div>
      </div>
    </div>
  );
}
