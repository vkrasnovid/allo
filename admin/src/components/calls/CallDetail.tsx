'use client';


import { BottomSheet } from '@/components/ui/BottomSheet';
import { Badge } from '@/components/ui/Badge';
import { AudioPlayer } from './AudioPlayer';
import { TranscriptionView } from './TranscriptionView';
import { Spinner } from '@/components/ui/Spinner';
import { formatPhone, formatDateTime, formatDuration, getResultBadgeVariant } from '@/lib/utils';
import { CALL_STATUS_LABELS } from '@/lib/types';
import type { Call } from '@/lib/types';

interface CallDetailProps {
  call: Call | null;
  open: boolean;
  onClose: () => void;
  loading?: boolean;
}

export function CallDetail({ call, open, onClose, loading }: CallDetailProps) {
  if (!open) return null;

  return (
    <BottomSheet open={open} onClose={onClose} title="Детали звонка">
      {loading ? (
        <div className="py-8"><Spinner /></div>
      ) : call ? (
        <div className="flex flex-col gap-5">
          {/* Info */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-text-tertiary mb-0.5">Номер</p>
              <p className="text-sm text-text-primary font-medium">{formatPhone(call.caller_phone)}</p>
            </div>
            <div>
              <p className="text-xs text-text-tertiary mb-0.5">Время</p>
              <p className="text-sm text-text-primary">{formatDateTime(call.created_at)}</p>
            </div>
            <div>
              <p className="text-xs text-text-tertiary mb-0.5">Длительность</p>
              <p className="text-sm text-text-primary">{formatDuration(call.duration_sec || 0)}</p>
            </div>
            <div>
              <p className="text-xs text-text-tertiary mb-0.5">Результат</p>
              <Badge variant={getResultBadgeVariant(call.result) as 'success' | 'warning' | 'error' | 'neutral'}>
                {CALL_STATUS_LABELS[call.result] || call.result}
              </Badge>
            </div>
          </div>

          {/* Audio */}
          <div>
            <p className="text-sm font-medium text-text-primary mb-2">Аудиозапись</p>
            <AudioPlayer audioUrl={call.audio_key} duration={call.duration_sec || 0} />
          </div>

          {/* Transcription */}
          <div>
            <p className="text-sm font-medium text-text-primary mb-2">Расшифровка</p>
            <TranscriptionView transcripts={call.transcript} />
          </div>

          {/* Result summary */}
          {call.result === 'booking_created' && call.client_name && (
            <div className="bg-success-bg rounded-md p-3">
              <p className="text-sm font-medium text-success-text">✅ Запись создана</p>
              <p className="text-sm text-success-text/80 mt-1">
                {call.client_name} записалась через Алло
              </p>
            </div>
          )}
          {call.result === 'escalated' && (
            <div className="bg-warning-bg rounded-md p-3">
              <p className="text-sm font-medium text-warning-text">⚠️ Эскалирован</p>
              <p className="text-sm text-warning-text/80 mt-1">
                Звонок переведён администратору
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className="py-8 text-center text-text-tertiary text-sm">Не удалось загрузить детали звонка</div>
      )}
    </BottomSheet>
  );
}
