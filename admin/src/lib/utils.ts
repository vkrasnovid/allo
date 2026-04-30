import { format, isToday, isTomorrow, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';

export function formatPhone(phone: string): string {
  // Simple phone formatting
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length === 11) {
    return `+${cleaned[0]} ${cleaned.slice(1,4)} ${cleaned.slice(4,7)}-${cleaned.slice(7,9)}-${cleaned.slice(9,11)}`;
  }
  return phone;
}

export function formatDate(dateStr: string): string {
  const date = parseISO(dateStr);
  if (isToday(date)) return 'Сегодня';
  if (isTomorrow(date)) return 'Завтра';
  return format(date, 'd MMMM', { locale: ru });
}

export function formatTime(dateStr: string): string {
  return format(parseISO(dateStr), 'HH:mm');
}

export function formatDateTime(dateStr: string): string {
  return format(parseISO(dateStr), 'd MMMM HH:mm', { locale: ru });
}

export function formatDuration(seconds: number): string {
  if (!seconds || seconds === 0) return '—';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m === 0) return `${s} с`;
  return `${m} мин ${s} с`;
}

export function formatPrice(rubles: number): string {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0,
  }).format(rubles);
}

export function getResultIcon(result: string): string {
  switch (result) {
    case 'booking_created': return '📅';
    case 'escalated': return '⚠️';
    case 'info_only': return '💬';
    case 'missed': return '📞';
    default: return '—';
  }
}

export function getResultBadgeVariant(result: string): string {
  switch (result) {
    case 'booking_created': return 'success';
    case 'escalated': return 'warning';
    case 'info_only': return 'neutral';
    case 'missed': return 'error';
    default: return 'neutral';
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'confirmed': return 'text-success';
    case 'pending': return 'text-warning';
    case 'cancelled':
    case 'no_show': return 'text-error';
    case 'completed': return 'text-text-tertiary';
    default: return 'text-text-tertiary';
  }
}

export function getStatusBgColor(status: string): string {
  switch (status) {
    case 'confirmed': return 'bg-success-bg text-success-text';
    case 'pending': return 'bg-warning-bg text-warning-text';
    case 'cancelled':
    case 'no_show': return 'bg-error-bg text-error-text';
    case 'completed': return 'bg-gray-100 text-gray-600';
    default: return 'bg-gray-100 text-gray-600';
  }
}

export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}
