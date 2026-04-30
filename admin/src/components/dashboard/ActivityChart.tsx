'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface ActivityPoint {
  date: string;
  calls: number;
  bookings: number;
}

interface ActivityChartProps {
  data: ActivityPoint[];
  loading?: boolean;
}

export function ActivityChart({ data, loading }: ActivityChartProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Звонки за неделю</CardTitle></CardHeader>
        <CardContent>
          <div className="h-48 skeleton-shimmer rounded-md" />
        </CardContent>
      </Card>
    );
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Звонки за неделю</CardTitle></CardHeader>
        <CardContent>
          <div className="h-48 flex items-center justify-center text-text-tertiary text-sm">
            Нет данных за период
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader><CardTitle>Звонки за неделю</CardTitle></CardHeader>
      <CardContent>
        <div className="h-48 md:h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} barGap={4} margin={{ top: 0, right: 0, left: -16, bottom: 0 }}>
              <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#9CA3AF' }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#9CA3AF' }} />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: '1px solid #E5E7EB', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.07)' }}
              />
              <Legend wrapperStyle={{ fontSize: 12, color: '#6B7280' }} />
              <Bar dataKey="calls" name="Звонки" fill="#8B5CF6" radius={[4, 4, 0, 0]} maxBarSize={32} />
              <Bar dataKey="bookings" name="Записи" fill="#A78BFA" radius={[4, 4, 0, 0]} maxBarSize={32} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
