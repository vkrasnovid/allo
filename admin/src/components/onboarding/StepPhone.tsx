'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';

interface StepPhoneProps {
  onNext: () => void;
  onBack: () => void;
}

const CITIES = [
  { value: 'moscow', label: 'Москва' },
  { value: 'spb', label: 'Санкт-Петербург' },
  { value: 'kazan', label: 'Казань' },
  { value: 'novosibirsk', label: 'Новосибирск' },
  { value: 'ekaterinburg', label: 'Екатеринбург' },
];

export function StepPhone({ onNext, onBack }: StepPhoneProps) {
  const [city, setCity] = useState('moscow');

  return (
    <div className="py-4">
      <h2 className="text-xl font-semibold text-text-primary mb-2">Какой у вас номер телефона?</h2>
      <p className="text-sm text-text-secondary mb-6">
        Алло даст вам новый номер, на который будут приходить звонки.
        После подключения вы настроите переадресацию со своего номера.
      </p>

      <div className="mb-6">
        <label className="text-sm font-medium text-text-primary block mb-1.5">
          Выберите город
        </label>
        <select
          value={city}
          onChange={e => setCity(e.target.value)}
          className="w-full h-11 md:h-10 px-3 rounded-sm border border-border bg-card text-text-primary text-base md:text-sm
                     focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none transition-colors"
        >
          {CITIES.map(c => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
        <p className="text-xs text-text-tertiary mt-1.5">
          После выбора города Алло подберёт доступный номер
        </p>
      </div>

      <div className="flex gap-3">
        <Button variant="ghost" onClick={onBack}>Назад</Button>
        <Button onClick={onNext} className="flex-1">Продолжить →</Button>
      </div>
    </div>
  );
}
