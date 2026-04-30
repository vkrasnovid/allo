'use client';

import { Button } from '@/components/ui/Button';
import { Mic } from 'lucide-react';

interface StepWelcomeProps {
  onNext: () => void;
  onSkip: () => void;
}

export function StepWelcome({ onNext, onSkip }: StepWelcomeProps) {
  return (
    <div className="flex flex-col items-center text-center py-8">
      <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mb-6">
        <Mic size={36} className="text-primary-500" />
      </div>

      <h1 className="text-2xl font-bold text-text-primary mb-3">
        Алло — голосовой секретарь вашего салона
      </h1>

      <p className="text-base text-text-secondary max-w-md mb-8 leading-relaxed">
        Принимает звонки, записывает клиентов, ничего не забывает.<br />
        Давайте подключим за 3 шага.
      </p>

      <Button size="lg" onClick={onNext} className="px-10">
        Начать →
      </Button>

      <button
        onClick={onSkip}
        className="mt-4 text-sm text-text-tertiary hover:text-text-secondary transition-colors underline underline-offset-2"
      >
        Настрою позже
      </button>
    </div>
  );
}
