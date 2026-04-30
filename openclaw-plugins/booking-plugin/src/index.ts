/**
 * Booking Plugin — OpenClaw TypeScript wrapper for Booking Service REST API.
 *
 * Each function proxies a tool call from Conversational Engine → Booking Service.
 * BOOKING_SERVICE_URL should be set via environment (default: http://booking:8003).
 */

const BASE_URL = process.env.BOOKING_SERVICE_URL || 'http://booking:8003';

interface RequestOptions {
  method: string;
  body?: unknown;
  params?: Record<string, string | undefined>;
}

async function request<T = unknown>(path: string, opts: RequestOptions = { method: 'GET' }): Promise<T> {
  let url = `${BASE_URL}/api/v1${path}`;

  if (opts.params) {
    const qs = Object.entries(opts.params)
      .filter(([, v]) => v !== undefined && v !== null)
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v!)}`)
      .join('&');
    if (qs) url += `?${qs}`;
  }

  const res = await fetch(url, {
    method: opts.method,
    headers: { 'Content-Type': 'application/json' },
    ...(opts.body ? { body: JSON.stringify(opts.body) } : {}),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'UNKNOWN', message: res.statusText }));
    throw new Error(`[BookingPlugin] ${res.status} ${err.error}: ${err.message}`);
  }

  return res.json() as Promise<T>;
}

// ─── Public API ──────────────────────────────────────────────────────────────

interface Service {
  id: string;
  name: string;
  description?: string;
  duration_min: number;
  price_rub: number;
  category?: string;
  is_active: boolean;
}

interface ServicesResponse {
  services: Service[];
}

export async function getServices(tenantId: string, category?: string): Promise<Service[]> {
  const data = await request<ServicesResponse>(`/tenants/${tenantId}/services`, {
    params: { category, is_active: 'true' },
  });
  return data.services;
}

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

export async function getMasters(tenantId: string, serviceId?: string): Promise<Master[]> {
  const data = await request<MastersResponse>(`/tenants/${tenantId}/masters`, {
    params: { service_id: serviceId, is_active: 'true' },
  });
  return data.masters;
}

export async function getMasterById(tenantId: string, masterId: string): Promise<Master | null> {
  const masters = await getMasters(tenantId);
  return masters.find((m) => m.id === masterId) ?? null;
}

interface TimeSlot {
  start: string;
  end: string;
  master_id: string;
  master_name: string;
}

interface SlotsResponse {
  slots: TimeSlot[];
}

export async function findSlots(
  tenantId: string,
  date: string,
  masterId?: string,
  serviceId?: string,
  days?: number,
): Promise<TimeSlot[]> {
  const data = await request<SlotsResponse>(`/tenants/${tenantId}/slots`, {
    params: {
      master_id: masterId,
      service_id: serviceId,
      date,
      days: days?.toString(),
    },
  });
  return data.slots;
}

interface BookingCreateParams {
  client_phone: string;
  client_name: string;
  master_id: string;
  service_id: string;
  start_at: string;
  comment?: string;
  source?: string;
}

interface BookingResponse {
  booking_id: string;
  status: string;
  summary: string;
  yclients_id?: number;
  client: { id: string; name?: string; phone: string };
  master: { name: string; id: string };
  service: { name: string; price_rub: number };
  start_at: string;
  end_at: string;
}

export async function createBooking(
  tenantId: string,
  params: BookingCreateParams,
): Promise<BookingResponse> {
  return request<BookingResponse>(`/tenants/${tenantId}/bookings`, {
    method: 'POST',
    body: {
      client_phone: params.client_phone,
      client_name: params.client_name,
      master_id: params.master_id,
      service_id: params.service_id,
      start_at: params.start_at,
      comment: params.comment,
      source: params.source || 'phone',
    },
  });
}

export async function findBooking(
  tenantId: string,
  clientPhone?: string,
  status?: string,
  limit?: number,
): Promise<BookingResponse[]> {
  const data = await request<{ bookings: BookingResponse[] }>(`/tenants/${tenantId}/bookings`, {
    params: { client_phone: clientPhone, status, limit: limit?.toString() },
  });
  return data.bookings;
}

export async function getBooking(
  tenantId: string,
  bookingId: string,
): Promise<BookingResponse | null> {
  try {
    return await request<BookingResponse>(`/tenants/${tenantId}/bookings/${bookingId}`);
  } catch {
    return null;
  }
}

interface BookingUpdateParams {
  action: 'reschedule' | 'cancel' | 'update_service' | 'update_master';
  start_at?: string;
  master_id?: string;
  service_id?: string;
  reason?: string;
}

interface UpdateResponse {
  booking_id: string;
  status: string;
  summary: string;
  changes: Record<string, unknown>;
}

export async function updateBooking(
  tenantId: string,
  bookingId: string,
  params: BookingUpdateParams,
): Promise<UpdateResponse> {
  return request<UpdateResponse>(`/tenants/${tenantId}/bookings/${bookingId}`, {
    method: 'PATCH',
    body: params,
  });
}

interface CancelResponse {
  booking_id: string;
  status: string;
  cancelled_at: string;
  penalty_info?: string;
}

export async function cancelBooking(
  tenantId: string,
  bookingId: string,
  reason?: string,
): Promise<CancelResponse> {
  const qs = reason ? `?reason=${encodeURIComponent(reason)}` : '';
  return request<CancelResponse>(`/tenants/${tenantId}/bookings/${bookingId}${qs}`, {
    method: 'DELETE',
  });
}

interface ClientByPhoneResponse {
  client?: {
    id: string;
    name?: string;
    phone: string;
    total_visits: number;
    last_visit_at?: string;
    preferences: Record<string, unknown>;
  };
  last_booking?: { service?: string; master?: string; date?: string } | null;
  error?: string;
}

export async function findClientByPhone(
  tenantId: string,
  phone: string,
): Promise<ClientByPhoneResponse> {
  return request<ClientByPhoneResponse>(`/tenants/${tenantId}/clients/by-phone/${encodeURIComponent(phone)}`);
}
