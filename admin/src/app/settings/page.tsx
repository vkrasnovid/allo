'use client';

import { useState, useEffect } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Card, CardTitle, CardContent } from '@/components/ui/Card';
import { SettingsSection } from '@/components/settings/SettingsSection';
import { Input, Textarea } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Toggle } from '@/components/ui/Toggle';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { ToastProvider, useToast } from '@/components/ui/Toast';
import { getSettings, updateSettings } from '@/lib/api';
import { formatPrice } from '@/lib/utils';
import type { AppSettings, Service, Master, PromptProfile, SipSettings, YClientsSettings, NotificationSettings } from '@/lib/types';
import { Settings as SettingsIcon, ChevronRight } from 'lucide-react';

function SettingsContent() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [error, setError] = useState(false);

  // Local state for editable fields
  const [prompt, setPrompt] = useState<PromptProfile | null>(null);
  const [notifications, setNotifications] = useState<NotificationSettings | null>(null);

  useEffect(() => {
    getSettings()
      .then(s => {
        setSettings(s);
        setPrompt(s.prompt);
        setNotifications(s.notifications);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const handleSavePrompt = async () => {
    if (!settings || !prompt) return;
    setSaving(true);
    try {
      const updated = await updateSettings({ ...settings, prompt });
      setSettings(updated);
      setPrompt(updated.prompt);
      toast('success', 'Настройки сохранены');
    } catch {
      toast('error', 'Не удалось сохранить настройки');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveNotifications = async () => {
    if (!settings || !notifications) return;
    setSaving(true);
    try {
      const updated = await updateSettings({ ...settings, notifications });
      setSettings(updated);
      setNotifications(updated.notifications);
      toast('success', 'Настройки уведомлений сохранены');
    } catch {
      toast('error', 'Не удалось сохранить настройки');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AppShell pageTitle="Настройки">
        <div className="py-12"><Spinner size="lg" /></div>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell pageTitle="Настройки">
        <div className="p-4 bg-error-bg rounded-md text-sm text-error-text text-center">
          Не удалось загрузить настройки.{' '}
          <button onClick={() => { setLoading(true); setError(false); }}
            className="underline font-medium">Попробовать снова</button>
        </div>
      </AppShell>
    );
  }

  // Empty/no-connection state
  if (settings && !settings.sip.is_active && !settings.yclients.is_connected) {
    return (
      <AppShell pageTitle="Настройки">
        <EmptyState
          icon={<SettingsIcon size={64} />}
          title="Подключение не настроено"
          description="Чтобы Алло начал работать, нужно пройти несколько шагов."
          action={{
            label: '🔄 Пройти настройку',
            onClick: () => window.location.href = '/onboarding',
          }}
        />
      </AppShell>
    );
  }

  return (
    <AppShell pageTitle="Настройки">
      <div className="flex flex-col gap-4 max-w-2xl">
        {/* Salon info */}
        <SettingsSection title="Салон">
          <div className="flex flex-col gap-3">
            <Input
              label="Название"
              value={settings?.tenant.name || ''}
              onChange={() => {}}
            />
            <Input
              label="Адрес"
              value={settings?.tenant.address || ''}
              onChange={() => {}}
            />
            <Input
              label="Телефон"
              value={settings?.tenant.phone || ''}
              onChange={() => {}}
            />
          </div>
        </SettingsSection>

        {/* Voice assistant */}
        <SettingsSection title="Голосовой секретарь">
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">Статус</p>
                <p className="text-xs text-text-tertiary">Алло принимает звонки</p>
              </div>
              <Badge variant="success">🟢 Активен</Badge>
            </div>

            {prompt && (
              <>
                <div>
                  <label className="text-sm font-medium text-text-primary block mb-1">Тон голоса</label>
                  <select
                    value={prompt.tone}
                    onChange={e => setPrompt({ ...prompt, tone: e.target.value as 'friendly' | 'formal' })}
                    className="w-full h-10 px-3 rounded-sm border border-border bg-card text-text-primary text-sm
                               focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none"
                  >
                    <option value="friendly">Дружелюбный</option>
                    <option value="formal">Строгий</option>
                  </select>
                </div>

                <Textarea
                  label="Приветствие"
                  value={prompt.greeting_text}
                  onChange={e => setPrompt({ ...prompt, greeting_text: e.target.value })}
                  rows={2}
                />

                <Button onClick={handleSavePrompt} loading={saving}>
                  Сохранить
                </Button>
              </>
            )}
          </div>
        </SettingsSection>

        {/* Bookings / CRM */}
        <SettingsSection title="Записи">
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">YClients</p>
                {settings?.yclients.last_sync_at && (
                  <p className="text-xs text-text-tertiary">
                    Последняя синхронизация: {new Date(settings.yclients.last_sync_at).toLocaleString('ru')}
                  </p>
                )}
              </div>
              <Badge variant={settings?.yclients.is_connected ? 'success' : 'error'}>
                {settings?.yclients.is_connected ? '🟢 Подключён' : '❌ Не подключён'}
              </Badge>
            </div>

            <Input
              label="API-ключ YClients"
              value="••••••••••••••••"
              onChange={() => {}}
              type="password"
            />

            <div>
              <p className="text-sm font-medium text-text-primary mb-2">Категории услуг</p>
              <div className="flex flex-wrap gap-2">
                {['Стрижки', 'Окрашивание', 'Маникюр', 'Педикюр', 'Косметология'].map(cat => (
                  <label key={cat} className="flex items-center gap-1.5 text-sm text-text-secondary">
                    <input type="checkbox" defaultChecked className="accent-primary-500 w-4 h-4" />
                    {cat}
                  </label>
                ))}
              </div>
            </div>
          </div>
        </SettingsSection>

        {/* Services */}
        <SettingsSection title="Услуги">
          <div className="flex flex-col gap-2">
            {settings?.services.map(s => (
              <div key={s.id} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                <div>
                  <p className="text-sm text-text-primary">{s.name}</p>
                  <p className="text-xs text-text-tertiary">{s.duration_min} мин · {formatPrice(s.price_rub)}</p>
                </div>
                <Badge variant={s.is_active ? 'success' : 'neutral'}>
                  {s.is_active ? 'Активна' : 'Неактивна'}
                </Badge>
              </div>
            ))}
          </div>
        </SettingsSection>

        {/* Masters */}
        <SettingsSection title="Команда">
          <div className="flex flex-col gap-2">
            {settings?.masters.map(m => (
              <div key={m.id} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                <div>
                  <p className="text-sm text-text-primary">{m.name}</p>
                  <p className="text-xs text-text-tertiary">{m.specialization || '—'}</p>
                </div>
                <ChevronRight size={16} className="text-text-tertiary" />
              </div>
            ))}
          </div>
        </SettingsSection>

        {/* Notifications */}
        <SettingsSection title="Уведомления">
          <div className="flex flex-col gap-1">
            {notifications && (
              <>
                <Toggle
                  label="Telegram-бот"
                  enabled={notifications.telegram_enabled}
                  onChange={v => setNotifications({ ...notifications, telegram_enabled: v })}
                />
                <Toggle
                  label="SMS клиентам"
                  enabled={notifications.sms_enabled}
                  onChange={v => setNotifications({ ...notifications, sms_enabled: v })}
                />
                <Toggle
                  label="Напоминание за день"
                  enabled={notifications.reminder_day}
                  onChange={v => setNotifications({ ...notifications, reminder_day: v })}
                />
                <Toggle
                  label="Напоминание за час"
                  enabled={notifications.reminder_hour}
                  onChange={v => setNotifications({ ...notifications, reminder_hour: v })}
                />
                <div className="mt-3">
                  <Button onClick={handleSaveNotifications} loading={saving} size="sm">
                    Сохранить
                  </Button>
                </div>
              </>
            )}
          </div>
        </SettingsSection>

        {/* System */}
        <SettingsSection title="О системе">
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-primary">Тариф</span>
              <Badge variant="primary">Базовый</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-primary">Номер</p>
                <p className="text-xs text-text-tertiary">{settings?.sip.did}</p>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-primary">Баланс</p>
                <p className="text-xs text-text-tertiary">Бесплатный период</p>
              </div>
            </div>
          </div>
        </SettingsSection>
      </div>
    </AppShell>
  );
}

export default function SettingsPage() {
  return (
    <ToastProvider>
      <SettingsContent />
    </ToastProvider>
  );
}
