'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface StepCRMSettingsProps {
  onNext: () => void;
  onBack: () => void;
}

export function StepCRMSettings({ onNext, onBack }: StepCRMSettingsProps) {
  const [crmType, setCrmType] = useState<'yclients' | 'none'>('yclients');
  const [apiKey, setApiKey] = useState('');

  return (
    <div className="py-4">
      <h2 className="text-xl font-semibold text-text-primary mb-2">Где вы ведёте записи?</h2>
      <p className="text-sm text-text-secondary mb-6">
        Алло может работать с вашей системой записей или вести свой календарь.
      </p>

      <div className="flex flex-col gap-3 mb-6">
        <label className={`
          flex items-center gap-3 p-4 rounded-md border-2 cursor-pointer transition-colors
          ${crmType === 'yclients' ? 'border-primary-500 bg-primary-50' : 'border-border hover:border-gray-300'}
        `}>
          <input
            type="radio"
            name="crm"
            value="yclients"
            checked={crmType === 'yclients'}
            onChange={() => setCrmType('yclients')}
            className="w-5 h-5 text-primary-500 accent-primary-500"
          />
          <div>
            <p className="font-medium text-text-primary text-sm">YClients</p>
            <p className="text-xs text-text-tertiary">Подключите ваш аккаунт YClients через API-ключ</p>
          </div>
        </label>

        <label className={`
          flex items-center gap-3 p-4 rounded-md border-2 cursor-pointer transition-colors
          ${crmType === 'none' ? 'border-primary-500 bg-primary-50' : 'border-border hover:border-gray-300'}
        `}>
          <input
            type="radio"
            name="crm"
            value="none"
            checked={crmType === 'none'}
            onChange={() => setCrmType('none')}
            className="w-5 h-5 text-primary-500 accent-primary-500"
          />
          <div>
            <p className="font-medium text-text-primary text-sm">Пока не используем</p>
            <p className="text-xs text-text-tertiary">Алло будет вести свой календарь записей</p>
          </div>
        </label>
      </div>

      {crmType === 'yclients' && (
        <div className="mb-6">
          <Input
            label="API-ключ YClients"
            value={apiKey}
            onChange={e => setApiKey(e.target.value)}
            placeholder="Вставьте API-ключ из YClients"
            helperText="Как получить ключ: нажмите на иконку ? в YClients"
          />
        </div>
      )}

      <div className="flex gap-3">
        <Button variant="ghost" onClick={onBack}>Назад</Button>
        <Button onClick={onNext} className="flex-1">Продолжить →</Button>
      </div>
    </div>
  );
}
