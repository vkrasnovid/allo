'use client';

import { useState, useEffect } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { BookingList } from '@/components/bookings/BookingList';
import { EmptyState } from '@/components/ui/EmptyState';
import { ToastProvider, useToast } from '@/components/ui/Toast';
import { getBookings, cancelBooking } from '@/lib/api';
import type { Booking } from '@/lib/types';
import { CalendarX } from 'lucide-react';

function BookingsContent() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    getBookings()
      .then(setBookings)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const handleCancel = async (id: string) => {
    if (!confirm('Отменить эту запись?')) return;
    try {
      await cancelBooking(id);
      setBookings(prev => prev.filter(b => b.id !== id));
      toast('success', 'Запись отменена');
    } catch {
      toast('error', 'Не удалось отменить запись');
    }
  };

  return (
    <AppShell pageTitle="Записи">
      {!loading && bookings.length === 0 && !error ? (
        <EmptyState
          icon={<CalendarX size={64} />}
          title="Записей пока нет"
          description="Клиенты ещё не записались через Алло. Как только появится первая запись, вы увидите её здесь."
        />
      ) : (
        <>
          <h2 className="text-base text-text-secondary hidden md:block mb-4">Все записи</h2>
          <BookingList
            bookings={bookings}
            loading={loading}
            onCancel={handleCancel}
          />
        </>
      )}

      {error && (
        <div className="mt-4 p-4 bg-error-bg rounded-md text-sm text-error-text text-center">
          Не удалось загрузить записи.{' '}
          <button onClick={() => { setLoading(true); setError(false); getBookings().then(setBookings).catch(() => setError(true)).finally(() => setLoading(false)); }}
            className="underline font-medium">Повторить загрузку</button>
        </div>
      )}
    </AppShell>
  );
}

export default function BookingsPage() {
  return (
    <ToastProvider>
      <BookingsContent />
    </ToastProvider>
  );
}
