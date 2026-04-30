'use client';

import { Button } from '@/components/ui/Button';
import { CheckCircle, Copy } from 'lucide-react';
import { useState } from 'react';

interface StepSuccessProps {
  onFinish: () => void;
  phoneNumber?: string;
}

export function StepSuccess({ onFinish, phoneNumber = '+7 495 123-45-67' }: StepSuccessProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(phoneNumber.replace(/[^+\d]/g, ''));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col items-center text-center py-8">
      <div className="w-20 h-20 bg-success-bg rounded-full flex items-center justify-center mb-6">
        <CheckCircle size={40} className="text-success" />
      </div>

      <h1 className="text-2xl font-bold text-text-primary mb-2">Всё готово!</h1>

      <p className="text-base text-text-secondary max-w-sm mb-6">
        Алло уже принимает звонки. Позвоните на тестовый номер, чтобы проверить:
      </p>

      <div className="flex items-center gap-2 bg-primary-50 rounded-md px-5 py-3 mb-8">
        <span className="text-xl font-bold text-primary-700 tracking-wider">{phoneNumber}</span>
        <button
          onClick={handleCopy}
          className="p-2 text-primary-500 hover:bg-primary-100 rounded-md transition-colors"
          title="Скопировать номер"
        >
          <Copy size={18} />
        </button>
      </div>
      {copied && (
        <p className="text-sm text-success -mt-6 mb-6">Номер скопирован!</p>
      )}

      <Button size="lg" onClick={onFinish} className="px-8">
        Открыть дашборд →
      </Button>
    </div>
  );
}
