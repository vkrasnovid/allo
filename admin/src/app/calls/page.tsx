'use client';

import { useState, useEffect } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { CallTable } from '@/components/calls/CallTable';
import { CallCard } from '@/components/calls/CallCard';
import { CallDetail } from '@/components/calls/CallDetail';
import { EmptyState } from '@/components/ui/EmptyState';
import { ToastProvider, useToast } from '@/components/ui/Toast';
import { getCalls, getCallDetails } from '@/lib/api';
import type { Call } from '@/lib/types';
import { PhoneOff } from 'lucide-react';

function CallsContent() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [calls, setCalls] = useState<Call[]>([]);
  const [selectedCall, setSelectedCall] = useState<Call | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    getCalls()
      .then(setCalls)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const handleSelect = async (call: Call) => {
    setDetailLoading(true);
    setDetailOpen(true);
    try {
      const details = await getCallDetails(call.id);
      setSelectedCall(details);
    } catch {
      toast('error', 'Не удалось загрузить детали звонка');
      setSelectedCall(call);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <AppShell pageTitle="Звонки">
      <div className="flex flex-col gap-3">
        <h2 className="text-base text-text-secondary hidden md:block">История звонков</h2>

        {!loading && calls.length === 0 && !error ? (
          <EmptyState
            icon={<PhoneOff size={64} />}
            title="Звонков пока нет"
            description="Алло ещё не принимал звонки на этот номер. Проверьте настройки подключения в разделе «Настройки»."
            action={{ label: 'Перейти к настройкам', onClick: () => window.location.href = '/settings' }}
          />
        ) : (
          <>
            {/* Desktop table */}
            <CallTable calls={calls} loading={loading} onSelect={handleSelect} />

            {/* Mobile cards */}
            <div className="flex flex-col gap-2 md:hidden">
              {loading ? (
                [1,2,3].map(i => <CallCard key={i} call={{} as import('@/lib/types').Call} loading onClick={() => {}} />)
              ) : (
                calls.map(call => (
                  <CallCard key={call.id} call={call} onClick={() => handleSelect(call)} />
                ))
              )}
            </div>
          </>
        )}

        {error && (
          <div className="p-4 bg-error-bg rounded-md text-sm text-error-text text-center">
            Не удалось загрузить список звонков.{' '}
            <button onClick={() => { setLoading(true); setError(false); getCalls().then(setCalls).catch(() => setError(true)).finally(() => setLoading(false)); }}
              className="underline font-medium">Повторить загрузку</button>
          </div>
        )}
      </div>

      {/* Detail bottom sheet / modal */}
      <CallDetail
        call={selectedCall}
        open={detailOpen}
        onClose={() => { setDetailOpen(false); setSelectedCall(null); }}
        loading={detailLoading}
      />
    </AppShell>
  );
}

export default function CallsPage() {
  return (
    <ToastProvider>
      <CallsContent />
    </ToastProvider>
  );
}
