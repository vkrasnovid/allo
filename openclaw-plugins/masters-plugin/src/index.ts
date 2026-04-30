/**
 * Masters Plugin — OpenClaw TypeScript wrapper for masters / escalations.
 *
 * BOOKING_SERVICE_URL should be set via environment (default: http://booking:8003).
 */

const BASE_URL = process.env.BOOKING_SERVICE_URL || 'http://booking:8003';

interface Master {
  id: string;
  name: string;
  phone?: string;
  specialization?: string;
  is_active: boolean;
}

interface MastersResponse {
  masters: Master[];
}

interface WorkingHours {
  'mon-fri': string;
  sat: string;
  sun: string;
}

interface BusinessInfoResponse {
  tenant_name: string;
  address?: string;
  phone: string;
  work_hours: WorkingHours;
  description?: string;
}

interface EscalateResponse {
  forward_to: string;
  action: string;
}

async function request<T = unknown>(
  path: string,
  opts: { method?: string; body?: unknown } = {},
): Promise<T> {
  const res = await fetch(`${BASE_URL}/api/v1${path}`, {
    method: opts.method || 'GET',
    headers: { 'Content-Type': 'application/json' },
    ...(opts.body ? { body: JSON.stringify(opts.body) } : {}),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'UNKNOWN' }));
    throw new Error(`[MastersPlugin] ${res.status} ${err.error}`);
  }
  return res.json() as Promise<T>;
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Получить всех мастеров салона. Опционально фильтр по услуге.
 */
export async function getMasters(tenantId: string, serviceId?: string): Promise<Master[]> {
  const qs = serviceId ? `?service_id=${encodeURIComponent(serviceId)}&is_active=true` : '?is_active=true';
  const data = await request<MastersResponse>(`/tenants/${tenantId}/masters${qs}`);
  return data.masters;
}

/**
 * Получить одного мастера по ID.
 */
export async function getMasterById(tenantId: string, masterId: string): Promise<Master | null> {
  const masters = await getMasters(tenantId);
  return masters.find((m) => m.id === masterId) ?? null;
}

/**
 * Получить расписание мастера на определённую дату.
 * Возвращает список свободных слотов для данного мастера.
 */
export async function getMasterSchedule(
  tenantId: string,
  masterId: string,
  date: string,
): Promise<{ start: string; end: string }[]> {
  const res = await fetch(
    `${BASE_URL}/api/v1/tenants/${tenantId}/slots?master_id=${encodeURIComponent(masterId)}&date=${encodeURIComponent(date)}`,
    { headers: { 'Content-Type': 'application/json' } },
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'UNKNOWN' }));
    throw new Error(`[MastersPlugin] ${res.status} ${err.error}`);
  }
  const data = await res.json() as { slots: { start: string; end: string }[] };
  return data.slots;
}

/**
 * Информация о салоне (название, адрес, часы работы).
 */
export async function getBusinessInfo(tenantId: string): Promise<BusinessInfoResponse> {
  return request<BusinessInfoResponse>(`/tenants/${tenantId}/info`);
}

/**
 * Эскалация звонка владельцу салона.
 */
export async function escalateToHuman(
  tenantId: string,
  callId: string,
  reason: string,
  clientSummary?: string,
): Promise<EscalateResponse> {
  return request<EscalateResponse>(`/tenants/${tenantId}/escalate`, {
    method: 'POST',
    body: { call_id: callId, reason, client_summary: clientSummary || '' },
  });
}
