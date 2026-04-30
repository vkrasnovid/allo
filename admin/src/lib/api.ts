// API client for Алло Backend (FastAPI)
// All endpoints return mock data for now (frontend-only MVP)

import type {
  Call, Booking, DashboardStats, ActivityPoint,
  Service, Master, AppSettings, OnboardingData
} from './types';

// ===== Mock Data (used when backend is unavailable) =====

const MOCK_CALLS: Call[] = [
  {
    id: '1', caller_phone: '+7 916 555-01-23', client_name: 'Мария С.',
    did: '+7 495 123-45-67', status: 'completed', duration_sec: 222,
    result: 'booking_created', created_at: new Date(Date.now() - 1000*60*15).toISOString(),
    ended_at: new Date(Date.now() - 1000*60*11).toISOString(),
    transcript: [
      { id: 't1', speaker: 'ai', text: 'Салон красоты "Элегия", Алло слушает!', start_sec: 0, end_sec: 2.5 },
      { id: 't2', speaker: 'client', text: 'Здравствуйте, хочу записаться на стрижку', start_sec: 3.0, end_sec: 6.0 },
      { id: 't3', speaker: 'ai', text: 'Конечно! На какое время вам удобно?', start_sec: 6.5, end_sec: 8.5 },
      { id: 't4', speaker: 'client', text: 'На завтра, после обеда', start_sec: 9.0, end_sec: 11.5 },
      { id: 't5', speaker: 'ai', text: 'Завтра есть свободное время в 14:00 у Елены. Вам подходит?', start_sec: 12.0, end_sec: 16.0 },
      { id: 't6', speaker: 'client', text: 'Да, отлично', start_sec: 16.5, end_sec: 17.5 },
      { id: 't7', speaker: 'ai', text: 'Записала вас к Елене на завтра в 14:00 на стрижку. Будем ждать!', start_sec: 18.0, end_sec: 22.0 },
    ],
  },
  {
    id: '2', caller_phone: '+7 903 555-45-67',
    did: '+7 495 123-45-67', status: 'completed', duration_sec: 95,
    result: 'info_only', created_at: new Date(Date.now() - 1000*60*45).toISOString(),
    ended_at: new Date(Date.now() - 1000*60*43).toISOString(),
    transcript: [
      { id: 't8', speaker: 'ai', text: 'Салон красоты "Элегия", Алло слушает!', start_sec: 0, end_sec: 2.5 },
      { id: 't9', speaker: 'client', text: 'Подскажите, сколько стоит маникюр?', start_sec: 3.0, end_sec: 5.0 },
      { id: 't10', speaker: 'ai', text: 'Маникюр у нас от 1500 рублей. Хотите записаться?', start_sec: 5.5, end_sec: 9.0 },
      { id: 't11', speaker: 'client', text: 'Нет, спасибо, я просто узнать. До свидания!', start_sec: 9.5, end_sec: 13.0 },
      { id: 't12', speaker: 'ai', text: 'Всего доброго! Если передумаете — перезвоните.', start_sec: 13.5, end_sec: 16.0 },
    ],
  },
  {
    id: '3', caller_phone: '+7 925 555-89-01', client_name: 'Антон К.',
    did: '+7 495 123-45-67', status: 'escalated', duration_sec: 180,
    result: 'escalated', created_at: new Date(Date.now() - 1000*60*120).toISOString(),
    ended_at: new Date(Date.now() - 1000*60*117).toISOString(),
    transcript: [
      { id: 't13', speaker: 'ai', text: 'Салон красоты "Элегия", Алло слушает!', start_sec: 0, end_sec: 2.5 },
      { id: 't14', speaker: 'client', text: 'Здравствуйте, у меня проблема с записью', start_sec: 3.0, end_sec: 5.5 },
      { id: 't15', speaker: 'ai', text: 'Извините, сейчас я соединю вас с администратором.', start_sec: 6.0, end_sec: 9.0 },
      { id: 't16', speaker: 'client', text: '...', start_sec: 9.0, end_sec: 10.0 },
    ],
  },
  {
    id: '4', caller_phone: '+7 916 555-67-89',
    did: '+7 495 123-45-67', status: 'completed', duration_sec: 45,
    result: 'missed', created_at: new Date(Date.now() - 1000*60*240).toISOString(),
    ended_at: new Date(Date.now() - 1000*60*239).toISOString(),
  },
  {
    id: '5', caller_phone: '+7 999 555-12-34', client_name: 'Елена В.',
    did: '+7 495 123-45-67', status: 'completed', duration_sec: 310,
    result: 'booking_created', created_at: new Date(Date.now() - 1000*60*360).toISOString(),
    ended_at: new Date(Date.now() - 1000*60*355).toISOString(),
  },
];

const MOCK_BOOKINGS: Booking[] = [
  {
    id: 'b1', client_name: 'Мария', client_phone: '+7 916 555-01-23',
    service_name: 'Стрижка + окрашивание', master_name: 'Елена',
    start_at: new Date(Date.now() + 1000*60*60*24).toISOString(),
    end_at: new Date(Date.now() + 1000*60*60*25.5).toISOString(),
    price_rub: 4500, status: 'confirmed', source: 'phone',
    created_at: new Date(Date.now() - 1000*60*15).toISOString(),
  },
  {
    id: 'b2', client_name: 'Анна', client_phone: '+7 903 555-45-67',
    service_name: 'Маникюр', master_name: 'Ольга',
    start_at: new Date(Date.now() + 1000*60*60*24 + 1000*60*90).toISOString(),
    end_at: new Date(Date.now() + 1000*60*60*24 + 1000*60*150).toISOString(),
    price_rub: 1500, status: 'pending', source: 'phone',
    created_at: new Date(Date.now() - 1000*60*45).toISOString(),
  },
  {
    id: 'b3', client_name: 'Елена В.', client_phone: '+7 999 555-12-34',
    service_name: 'Стрижка', master_name: 'Анна',
    start_at: new Date(Date.now() + 1000*60*60*48).toISOString(),
    end_at: new Date(Date.now() + 1000*60*60*49).toISOString(),
    price_rub: 2500, status: 'confirmed', source: 'phone',
    created_at: new Date(Date.now() - 1000*60*360).toISOString(),
  },
];

const MOCK_SERVICES: Service[] = [
  { id: 's1', name: 'Стрижка женская', duration_min: 60, price_rub: 2500, category: 'Стрижки', is_active: true },
  { id: 's2', name: 'Стрижка мужская', duration_min: 40, price_rub: 1500, category: 'Стрижки', is_active: true },
  { id: 's3', name: 'Окрашивание', duration_min: 120, price_rub: 4500, category: 'Окрашивание', is_active: true },
  { id: 's4', name: 'Маникюр', duration_min: 60, price_rub: 1500, category: 'Маникюр', is_active: true },
  { id: 's5', name: 'Педикюр', duration_min: 60, price_rub: 2000, category: 'Педикюр', is_active: true },
  { id: 's6', name: 'Косметология', duration_min: 90, price_rub: 3500, category: 'Косметология', is_active: true },
];

const MOCK_MASTERS: Master[] = [
  { id: 'm1', name: 'Елена', phone: '+7 916 111-11-11', specialization: 'Стрижки, окрашивание', is_active: true },
  { id: 'm2', name: 'Ольга', phone: '+7 916 222-22-22', specialization: 'Маникюр, педикюр', is_active: true },
  { id: 'm3', name: 'Анна', phone: '+7 916 333-33-33', specialization: 'Косметолог', is_active: true },
];

const MOCK_SETTINGS: AppSettings = {
  tenant: { id: 't1', name: 'Студия красоты "Элегия"', phone: '+7 495 123-45-67', address: 'ул. Тверская, 15', timezone: 'Europe/Moscow', status: 'active' },
  prompt: { salon_name: 'Студия красоты "Элегия"', greeting_text: 'Студия красоты "Элегия", Алло у телефона!', tone: 'friendly', ai_name: 'Алло', rules: 'Не записывать новых клиентов после 20:00', farewell: 'Будем ждать вас! Всего доброго!' },
  sip: { did: '+7 495 123-45-67', forward_number: '+7 916 555-00-00', is_active: true },
  yclients: { is_connected: true, last_sync_at: new Date().toISOString() },
  notifications: { telegram_enabled: true, sms_enabled: true, reminder_day: true, reminder_hour: true },
  services: MOCK_SERVICES,
  masters: MOCK_MASTERS,
  work_hours: { mon_fri: '09:00-21:00', sat: '10:00-20:00', sun: '10:00-18:00' },
};

// ===== API Functions =====

const mockDelay = 600; // ms delay to simulate network

function delay(ms = mockDelay): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export async function getDashboardStats(_tenantId?: string): Promise<DashboardStats> {
  await delay();
  return { total_calls: 42, total_bookings: 18, total_escalations: 3, answer_rate: 94, period_start: '', period_end: '' };
}

export async function getDashboardActivity(_tenantId?: string): Promise<ActivityPoint[]> {
  await delay();
  return [
    { date: 'Пн', calls: 5, bookings: 3 },
    { date: 'Вт', calls: 8, bookings: 4 },
    { date: 'Ср', calls: 3, bookings: 1 },
    { date: 'Чт', calls: 9, bookings: 5 },
    { date: 'Пт', calls: 12, bookings: 4 },
    { date: 'Сб', calls: 4, bookings: 1 },
    { date: 'Вс', calls: 1, bookings: 0 },
  ];
}

export async function getCalls(_tenantId?: string): Promise<Call[]> {
  await delay(400);
  return MOCK_CALLS;
}

export async function getCallDetails(id: string): Promise<Call> {
  await delay(500);
  const call = MOCK_CALLS.find(c => c.id === id);
  if (!call) throw new Error('Call not found');
  return call;
}

export async function getBookings(_tenantId?: string): Promise<Booking[]> {
  await delay(400);
  return MOCK_BOOKINGS;
}

export async function cancelBooking(id: string): Promise<void> {
  await delay(300);
  console.log('Booking cancelled:', id);
}

export async function getSettings(_tenantId?: string): Promise<AppSettings> {
  await delay(500);
  return MOCK_SETTINGS;
}

export async function updateSettings(data: Partial<AppSettings>): Promise<AppSettings> {
  await delay(800);
  Object.assign(MOCK_SETTINGS, data);
  return MOCK_SETTINGS;
}

export async function saveOnboarding(data: OnboardingData): Promise<void> {
  await delay(1200);
  console.log('Onboarding saved:', data);
}

export async function getActivityChartData(): Promise<ActivityPoint[]> {
  await delay();
  return getDashboardActivity();
}
