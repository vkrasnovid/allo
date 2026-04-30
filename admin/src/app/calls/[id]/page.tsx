'use client';

import { useState, useEffect, use } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Card, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { AudioPlayer } from '@/components/calls/AudioPlayer';
import { TranscriptionView } from '@/components/calls/TranscriptionView';
import { Spinner } from '@/components/ui/Spinner';
import { Button } from '@/components/ui/Button';
import { getCallDetails } from '@/lib/api';
import { formatPhone, formatDateTime, formatDuration, getResultBadgeVariant } from '@/lib/utils';
import { CALL_STATUS_LABELS } from '@/lib/types';
import type { Call } from '@/lib/types';
import { ArrowLeft, Edit3 } from 'lucide-react';
import Link from 'next/link';

interface CallDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function CallDetailPage({ params }: CallDetailPageProps) {
  const { id } = use(params);
  const [call, setCall] = useState<Call | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    getCallDetails(id)
      .then(setCall)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <AppShell pageTitle="Детали звонка">
      <Link href="/calls" className="inline-flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary mb-4 transition-colors">
        <ArrowLeft size={16} /> Назад к звонкам
      </Link>

      {loading ? (
        <div className="py-12"><Spinner size="lg" /></div>
      ) : error ? (
        <div className="p-4 bg-error-bg rounded-md text-sm text-error-text text-center">
          Не удалось загрузить детали звонка.{' '}
          <button onClick={() => { setLoading(true); setError(false); }}
            className="underline font-medium">Попробовать снова</button>
        </div>
      ) : call ? (
        <div className="flex flex-col gap-4 md:gap-6 max-w-2xl">
          {/* Call info */}
          <Card>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-text-tertiary mb-0.5">Номер</p>
                <p className="text-sm font-medium text-text-primary">{formatPhone(call.caller_phone)}</p>
              </div>
              {call.client_name && (
                <div>
                  <p className="text-xs text-text-tertiary mb-0.5">Клиент</p>
                  <p className="text-sm font-medium text-text-primary">{call.client_name}</p>
                </div>
              )}
              <div>
                <p className="text-xs text-text-tertiary mb-0.5">Время</p>
                <p className="text-sm text-text-primary">{formatDateTime(call.created_at)}</p>
              </div>
              <div>
                <p className="text-xs text-text-tertiary mb-0.5">Длительность</p>
                <p className="text-sm text-text-primary">{formatDuration(call.duration_sec || 0)}</p>
              </div>
              <div>
                <p className="text-xs text-text-tertiary mb-0.5">Статус</p>
                <Badge variant={getResultBadgeVariant(call.result) as 'success' | 'warning' | 'error' | 'neutral'}>
                  {CALL_STATUS_LABELS[call.result] || call.result}
                </Badge>
              </div>
            </div>
          </Card>

          {/* Audio */}
          <Card>
            <CardTitle className="text-sm mb-3">Аудиозапись</CardTitle>
            <AudioPlayer audioUrl={call.audio_key} duration={call.duration_sec || 0} />
          </Card>

          {/* Transcription */}
          <Card>
            <CardTitle className="text-sm mb-3">Расшифровка</CardTitle>
            <TranscriptionView transcripts={call.transcript} />
          </Card>

          {/* Result */}
          {call.result === 'booking_created' && (
            <Card>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">✅</span>
                  <div>
                    <p className="text-sm font-medium text-text-primary">Запись создана</p>
                    <p className="text-xs text-text-tertiary">
                      {call.client_name || 'Клиент'} — создана запись
                    </p>
                  </div>
                </div>
                <Button variant="secondary" size="sm">
                  <Edit3 size={14} /> Редактировать
                </Button>
              </div>
            </Card>
          )}
          {call.result === 'escalated' && (
            <Card>
              <div className="flex items-center gap-2">
                <span className="text-lg">⚠️</span>
                <div>
                  <p className="text-sm font-medium text-text-primary">Эскалирован</p>
                  <p className="text-xs text-text-tertiary">
                    Звонок переведён администратору
                  </p>
                </div>
              </div>
            </Card>
          )}
        </div>
      ) : null}
    </AppShell>
  );
}
