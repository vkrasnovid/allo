// ===== Core Types for Алло Admin Panel =====

export interface Tenant {
  id: string;
  name: string;
  phone: string;
  address?: string;
  timezone: string;
  status: 'active' | 'suspended';
}

export interface Call {
  id: string;
  caller_phone: string;
  client_name?: string;
  did: string;
  status: 'in_progress' | 'completed' | 'failed' | 'escalated' | 'missed';
  duration_sec?: number;
  result: 'booking_created' | 'info_only' | 'escalated' | 'cancelled' | 'missed';
  audio_key?: string;
  created_at: string;
  ended_at?: string;
  transcript?: CallTranscript[];
}

export interface CallTranscript {
  id: string;
  speaker: 'ai' | 'client';
  text: string;
  start_sec: number;
  end_sec: number;
  tool_calls?: Record<string, unknown>;
}

export interface Booking {
  id: string;
  client_name: string;
  client_phone: string;
  service_name: string;
  master_name: string;
  start_at: string;
  end_at: string;
  price_rub: number;
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'no_show';
  source: 'phone' | 'telegram' | 'admin';
  comment?: string;
  created_at: string;
}

export interface DashboardStats {
  total_calls: number;
  total_bookings: number;
  total_escalations: number;
  answer_rate: number;
  period_start: string;
  period_end: string;
}

export interface ActivityPoint {
  date: string;
  calls: number;
  bookings: number;
}

export interface Service {
  id: string;
  name: string;
  description?: string;
  duration_min: number;
  price_rub: number;
  category: string;
  is_active: boolean;
}

export interface Master {
  id: string;
  name: string;
  phone?: string;
  specialization?: string;
  is_active: boolean;
}

export interface PromptProfile {
  salon_name: string;
  greeting_text: string;
  tone: 'friendly' | 'formal';
  ai_name: string;
  rules: string;
  farewell: string;
}

export interface SipSettings {
  did: string;
  forward_number?: string;
  is_active: boolean;
}

export interface YClientsSettings {
  api_key?: string;
  is_connected: boolean;
  last_sync_at?: string;
}

export interface NotificationSettings {
  telegram_enabled: boolean;
  sms_enabled: boolean;
  reminder_day: boolean;
  reminder_hour: boolean;
}

export interface AppSettings {
  tenant: Tenant;
  prompt: PromptProfile;
  sip: SipSettings;
  yclients: YClientsSettings;
  notifications: NotificationSettings;
  services: Service[];
  masters: Master[];
  work_hours: {
    mon_fri?: string;
    sat?: string;
    sun?: string;
  };
}

// Onboarding state
export interface OnboardingData {
  phone: {
    city: string;
  };
  crm: {
    type: 'yclients' | 'other' | 'none';
    api_key?: string;
  };
  greeting: {
    salon_name: string;
    tone: 'friendly' | 'formal';
    ai_name: string;
    rules: string;
  };
}

export type OnboardingStep = 1 | 2 | 3 | 4;

export const ONBOARDING_STEPS = [
  { id: 1, label: 'Номер телефона' },
  { id: 2, label: 'Подключение записей' },
  { id: 3, label: 'Приветствие' },
  { id: 4, label: 'Готово!' },
] as const;

export const CALL_STATUS_LABELS: Record<string, string> = {
  booking_created: 'Записан',
  info_only: 'Справка',
  escalated: 'Эскалация',
  cancelled: 'Отказ',
  missed: 'Пропущен',
  in_progress: 'В процессе',
  completed: 'Завершён',
  failed: 'Ошибка',
};

export const BOOKING_STATUS_LABELS: Record<string, string> = {
  pending: 'Ожидает',
  confirmed: 'Подтверждена',
  completed: 'Выполнена',
  cancelled: 'Отменена',
  no_show: 'Не явился',
};

export const BOOKING_STATUS_VARIANTS: Record<string, 'success' | 'warning' | 'neutral' | 'error'> = {
  confirmed: 'success',
  pending: 'warning',
  completed: 'neutral',
  cancelled: 'error',
  no_show: 'error',
};

export type BadgeVariant = 'success' | 'warning' | 'error' | 'neutral' | 'primary';
