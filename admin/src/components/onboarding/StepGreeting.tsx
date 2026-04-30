'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';

interface StepGreetingProps {
  onNext: () => void;
  onBack: () => void;
}

export function StepGreeting({ onNext, onBack }: StepGreetingProps) {
  const [salonName, setSalonName] = useState('Студия красоты "Элегия"');
  const [tone, setTone] = useState<'friendly' | 'formal'>('friendly');
  const [rules, setRules] = useState('Не записывать новых клиентов после 20:00');

  return (
    <div className="py-4">
      <h2 className="text-xl font-semibold text-text-primary mb-2">Как Алло будет отвечать?</h2>
      <p className="text-sm text-text-secondary mb-6">
        Настройте голос вашего секретаря. Всё можно будет изменить позже.
      </p>

      <div className="flex flex-col gap-5">
        <Input
          label="Название салона"
          value={salonName}
          onChange={e => setSalonName(e.target.value)}
          placeholder="Например: Салон красоты «Роза»"
        />

        <div>
          <label className="text-sm font-medium text-text-primary block mb-2">Тон разговора</label>
          <div className="flex gap-3">
            <button
              onClick={() => setTone('friendly')}
              className={`flex-1 py-2.5 px-4 rounded-md border-2 text-sm font-medium transition-colors text-center
                ${tone === 'friendly' ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-border text-text-secondary hover:border-gray-300'}`}
            >
              Дружелюбный
            </button>
            <button
              onClick={() => setTone('formal')}
              className={`flex-1 py-2.5 px-4 rounded-md border-2 text-sm font-medium transition-colors text-center
                ${tone === 'formal' ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-border text-text-secondary hover:border-gray-300'}`}
            >
              Строгий
            </button>
          </div>
        </div>

        <Textarea
          label="Особые пожелания"
          value={rules}
          onChange={e => setRules(e.target.value)}
          placeholder="Например: не записывать новых клиентов после 20:00"
          rows={3}
        />
      </div>

      <div className="flex gap-3 mt-6">
        <Button variant="ghost" onClick={onBack}>Назад</Button>
        <Button onClick={onNext} className="flex-1">Готово 🎉</Button>
      </div>
    </div>
  );
}
