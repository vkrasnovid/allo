'use client';

import { useMemo, useState } from 'react';
import { BookingCard } from './BookingCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { CalendarX } from 'lucide-react';
import { format, parseISO, isAfter } from 'date-fns';
import { ru } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import type { Booking } from '@/lib/types';

interface BookingListProps {
  bookings: Booking[];
  loading?: boolean;
  onCancel?: (id: string) => void;
}

type FilterType = 'all' | 'today' | 'tomorrow' | 'upcoming';

const FILTERS: { key: FilterType; label: string }[] = [
  { key: 'all', label: 'Все' },
  { key: 'today', label: 'Сегодня' },
  { key: 'tomorrow', label: 'Завтра' },
  { key: 'upcoming', label: 'Ближайшие' },
];

export function BookingList({ bookings, loading, onCancel }: BookingListProps) {
  const [filter, setFilter] = useState<FilterType>('all');

  const grouped = useMemo(() => {
    let filtered = bookings;
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const tomorrow = new Date(today.getTime() + 86400000);

    if (filter === 'today') {
      filtered = bookings.filter(b => {
        const d = parseISO(b.start_at);
        return d >= today && d < tomorrow;
      });
    } else if (filter === 'tomorrow') {
      filtered = bookings.filter(b => {
        const d = parseISO(b.start_at);
        return d >= tomorrow && d < new Date(tomorrow.getTime() + 86400000);
      });
    } else if (filter === 'upcoming') {
      filtered = bookings.filter(b => isAfter(parseISO(b.start_at), now));
    }

    // Group by date
    const groups: Record<string, Booking[]> = {};
    filtered.forEach(b => {
      const dateKey = format(parseISO(b.start_at), 'yyyy-MM-dd');
      if (!groups[dateKey]) groups[dateKey] = [];
      groups[dateKey].push(b);
    });

    return Object.entries(groups)
      .sort(([a], [_b]) => a.localeCompare(_b))
      .map(([date, items]) => ({
        dateLabel: format(parseISO(items[0].start_at), 'd MMMM', { locale: ru }),
        items,
      }));
  }, [bookings, filter]);

  if (loading) {
    return (
      <div className="flex flex-col gap-3">
        {[1,2,3].map(i => <BookingCard key={i} booking={{} as import('@/lib/types').Booking} loading />)}
      </div>
    );
  }

  return (
    <div>
      {/* Filters */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
        {FILTERS.map(f => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={cn(
              'px-3 py-1.5 rounded-pill text-sm font-medium whitespace-nowrap transition-colors',
              filter === f.key
                ? 'bg-primary-100 text-primary-700'
                : 'bg-gray-100 text-text-secondary hover:bg-gray-200'
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {grouped.length === 0 ? (
        <EmptyState
          icon={<CalendarX size={48} />}
          title="Записей пока нет"
          description="Клиенты ещё не записались через Алло."
        />
      ) : (
        <div className="flex flex-col gap-4">
          {grouped.map(group => (
            <div key={group.dateLabel}>
              <h3 className="text-sm font-medium text-text-secondary mb-2">{group.dateLabel}</h3>
              <div className="flex flex-col gap-2">
                {group.items.map(booking => (
                  <BookingCard key={booking.id} booking={booking} onCancel={onCancel} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
