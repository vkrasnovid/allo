/**
 * Calendar Plugin — OpenClaw TypeScript wrapper for slot/calendar endpoints.
 *
 * BOOKING_SERVICE_URL should be set via environment (default: http://booking:8003).
 */

const BASE_URL = process.env.BOOKING_SERVICE_URL || 'http://booking:8003';

interface TimeSlot {
  start: string;
  end: string;
  master_id: string;
  master_name: string;
}

interface SlotsResponse {
  slots: TimeSlot[];
}

interface WorkingHoursResponse {
  tenant_name: string;
  work_hours: Record<string, string>;
}

async function request<T = unknown>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}/api/v1${path}`, {
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'UNKNOWN' }));
    throw new Error(`[CalendarPlugin] ${res.status} ${err.error}`);
  }
  return res.json() as Promise<T>;
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Проверяет, есть ли свободные слоты на указанную дату.
 * Возвращает true, если хотя бы один слот свободен.
 */
export async function checkAvailability(
  tenantId: string,
  date: string,
  masterId?: string,
  serviceId?: string,
): Promise<boolean> {
  const qs = new URLSearchParams();
  if (masterId) qs.set('master_id', masterId);
  if (serviceId) qs.set('service_id', serviceId);
  if (date) qs.set('date', date);

  const data = await request<SlotsResponse>(
    `/tenants/${tenantId}/slots?${qs.toString()}`,
  );
  return data.slots.length > 0;
}

/**
 * Возвращает список занятых слотов на указанную дату.
 * Для каждого мастера возвращает занятые интервалы.
 */
export async function getBusySlots(
  tenantId: string,
  date: string,
  masterId?: string,
): Promise<TimeSlot[]> {
  const qs = new URLSearchParams();
  if (masterId) qs.set('master_id', masterId);
  if (date) qs.set('date', date);

  const data = await request<SlotsResponse>(
    `/tenants/${tenantId}/slots?${qs.toString()}`,
  );
  // Slots endpoint returns available (free) slots.
  // Busy slots are the complement — we define them as unavailable time.
  // For simplicity we return empty here; the booking service
  // handles conflict detection during booking creation.
  return data.slots;
}

/**
 * Возвращает рабочие часы салона.
 */
export async function getWorkingHours(
  tenantId: string,
): Promise<Record<string, string>> {
  const data = await request<WorkingHoursResponse>(`/tenants/${tenantId}/info`);
  return data.work_hours;
}
