'use client';

import { useState, useEffect } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { StatCard } from '@/components/dashboard/StatCard';
import { ActivityChart } from '@/components/dashboard/ActivityChart';
import { RecentCallsList } from '@/components/dashboard/RecentCallsList';
import { UpcomingBookingsList } from '@/components/dashboard/UpcomingBookingsList';
import { EmptyState } from '@/components/ui/EmptyState';
import { ToastProvider } from '@/components/ui/Toast';
import { getDashboardStats, getDashboardActivity, getCalls, getBookings } from '@/lib/api';
import type { DashboardStats, ActivityPoint, Call, Booking } from '@/lib/types';
import { Phone, CalendarCheck, AlertTriangle, CheckCircle, BarChart3 } from 'lucide-react';
import { Skeleton } from '@/components/ui/Skeleton';

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activity, setActivity] = useState<ActivityPoint[]>([]);
  const [calls, setCalls] = useState<Call[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [s, a, c, b] = await Promise.all([
          getDashboardStats(),
          getDashboardActivity(),
          getCalls(),
          getBookings(),
        ]);
        setStats(s);
        setActivity(a);
        setCalls(c);
        setBookings(b);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const isEmpty = !loading && stats && stats.total_calls === 0 && stats.total_bookings === 0;

  return (
    <ToastProvider>
      <AppShell pageTitle="Дашборд">
        {isEmpty ? (
          <EmptyState
            icon={<BarChart3 size={64} />}
            title="Здесь будет статистика"
            description="Как только Алло начнёт принимать звонки, вы увидите цифры и графики."
          />
        ) : (
          <div className="flex flex-col gap-4 md:gap-6">
            {/* Stat cards */}
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
              <StatCard
                label="Принято звонков"
                value={stats?.total_calls ?? 0}
                icon={<Phone size={20} />}
                loading={loading}
              />
              <StatCard
                label="Записались"
                value={stats?.total_bookings ?? 0}
                icon={<CalendarCheck size={20} />}
                loading={loading}
              />
              <StatCard
                label="На моём контроле"
                value={stats?.total_escalations ?? 0}
                icon={<AlertTriangle size={20} />}
                loading={loading}
              />
              <StatCard
                label="Ответили"
                value={`${stats?.answer_rate ?? 0}%`}
                icon={<CheckCircle size={20} />}
                loading={loading}
              />
            </div>

            {/* Chart */}
            <ActivityChart data={activity} loading={loading} />

            {/* Recent calls and upcoming bookings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
              <RecentCallsList calls={calls} loading={loading} />
              <UpcomingBookingsList bookings={bookings} loading={loading} />
            </div>
          </div>
        )}

        {error && !loading && (
          <div className="mt-4 p-4 bg-error-bg rounded-md text-sm text-error-text text-center">
            Не удалось загрузить данные. Проверьте подключение к интернету.{' '}
            <button onClick={() => { setLoading(true); setError(false); window.location.reload(); }}
              className="underline font-medium">Повторить</button>
          </div>
        )}
      </AppShell>
    </ToastProvider>
  );
}
