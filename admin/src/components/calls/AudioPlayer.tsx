'use client';

import { useState } from 'react';
import { Play, Pause, Download } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AudioPlayerProps {
  audioUrl?: string;
  duration: number;
}

export function AudioPlayer({ audioUrl, duration }: AudioPlayerProps) {
  const [playing, setPlaying] = useState(false);
  const [currentTime] = useState(0);

  // Simulated playback (no real audio without backend)
  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  const togglePlay = () => {
    if (!audioUrl) return;
    setPlaying(!playing);
    // In real app: audioRef.current?.play() / pause()
  };

  const formatTime_ = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-gray-50 rounded-md p-3">
      <div className="flex items-center gap-3">
        <button
          onClick={togglePlay}
          disabled={!audioUrl}
          className={cn(
            'w-9 h-9 rounded-full flex items-center justify-center shrink-0',
            audioUrl ? 'bg-primary-500 text-white hover:bg-primary-600' : 'bg-gray-200 text-text-tertiary cursor-not-allowed'
          )}
        >
          {playing ? <Pause size={16} /> : <Play size={16} />}
        </button>
        <div className="flex-1">
          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-500 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between mt-1 text-xs text-text-tertiary">
            <span>{formatTime_(currentTime)}</span>
            <span>{formatTime_(duration)}</span>
          </div>
        </div>
        {audioUrl && (
          <button className="p-2 text-text-tertiary hover:text-text-primary transition-colors" title="Скачать">
            <Download size={16} />
          </button>
        )}
      </div>
      {!audioUrl && (
        <p className="text-xs text-text-tertiary mt-2 text-center">
          Аудиозапись недоступна (срок хранения истёк)
        </p>
      )}
    </div>
  );
}
