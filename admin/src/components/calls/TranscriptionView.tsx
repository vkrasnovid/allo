'use client';

import { cn } from '@/lib/utils';
import { SkeletonText } from '@/components/ui/Skeleton';
import { Phone, User } from 'lucide-react';
import type { CallTranscript } from '@/lib/types';

interface TranscriptionViewProps {
  transcripts?: CallTranscript[];
  loading?: boolean;
}

export function TranscriptionView({ transcripts, loading }: TranscriptionViewProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-3">
        {[1,2,3,4].map(i => (
          <div key={i} className="flex gap-2">
            <SkeletonText lines={1} />
          </div>
        ))}
      </div>
    );
  }

  if (!transcripts || transcripts.length === 0) {
    return (
      <p className="text-sm text-text-tertiary text-center py-4">Расшифровка отсутствует</p>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {transcripts.map(t => (
        <div
          key={t.id}
          className={cn(
            'flex gap-2 p-2 rounded-sm text-sm',
            t.speaker === 'ai' ? 'bg-primary-50' : 'bg-gray-50'
          )}
        >
          <div className="shrink-0 mt-0.5">
            {t.speaker === 'ai' ? (
              <Phone size={14} className="text-primary-500" />
            ) : (
              <User size={14} className="text-text-secondary" />
            )}
          </div>
          <div className="flex-1">
            <p className="text-xs font-medium mb-0.5 text-text-secondary">
              {t.speaker === 'ai' ? 'Алло' : 'Клиент'}
              {t.start_sec != null && (
                <span className="text-text-tertiary ml-2 font-normal">
                  {formatSec(t.start_sec)} – {formatSec(t.end_sec || t.start_sec)}
                </span>
              )}
            </p>
            <p className="text-text-primary">{t.text}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function formatSec(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}
