# API Reference — Алло (Allo) Voice AI Secretary

> Service-to-service API contracts for the Алло voice AI secretary platform.
> All APIs are internal unless marked as external.

---

## Table of Contents

1. [Booking Service API](#1-booking-service-api)
   - [Bookings](#bookings)
   - [Slots](#slots)
   - [Clients](#clients)
   - [Services & Masters](#services--masters)
   - [Business Info](#business-info)
   - [Escalation](#escalation)
   - [Error Reference](#error-reference)
2. [Engine Service API](#2-engine-service-api)
3. [Speech Service API](#3-speech-service-api)
4. [Gateway API](#4-gateway-api)
5. [Admin Panel API](#5-admin-panel-api)

---

## 1. Booking Service API

**Base URL:** `http://booking:8003/api/v1/tenants/{tenant_id}`

**Headers:**

| Header | Required | Value |
|--------|----------|-------|
| `Content-Type` | ✅ | `application/json` |
| `X-Internal-API-Key` | ✅ | Internal API key for service-to-service auth |

All endpoints are scoped to a tenant. The `{tenant_id}` path parameter identifies which salon the request targets.

**Common error responses:**

```json
// 401 Unauthorized — missing or invalid API key
{ "error": "UNAUTHORIZED", "message": "Invalid or missing API key" }

// 403 Forbidden — tenant is suspended
{ "error": "TENANT_INACTIVE", "message": "Tenant is not active" }

// 404 Not Found — tenant doesn't exist
{ "error": "TENANT_NOT_FOUND", "message": "Tenant not found" }

// 429 Too Many Requests — rate limit exceeded
{ "error": "RATE_LIMITED", "message": "Too many requests. Try again later" }
```

---

### Bookings

#### GET /bookings

List bookings for a tenant.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | UUID | No | Filter by client |
| `master_id` | UUID | No | Filter by master |
| `status` | string | No | `pending`, `confirmed`, `completed`, `cancelled`, `no_show` |
| `date_from` | ISO 8601 | No | Start of date range |
| `date_to` | ISO 8601 | No | End of date range |
| `limit` | int | No | Max results (default: 50, max: 200) |
| `offset` | int | No | Pagination offset (default: 0) |

**Response `200 OK`:**

```json
{
  "bookings": [
    {
      "id": "3f5e8c2a-1b4d-4f7e-9a6c-8d3e2f1a0b5c",
      "status": "confirmed",
      "client": {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name": "Мария Иванова",
        "phone": "+79161234567"
      },
      "master": {
        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "name": "Анна Петрова"
      },
      "service": {
        "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "name": "Стрижка женская",
        "price_rub": 2500.00,
        "duration_min": 60
      },
      "start_at": "2026-05-15T14:00:00+03:00",
      "end_at": "2026-05-15T15:00:00+03:00",
      "comment": null,
      "source": "phone",
      "yclients_id": 98765,
      "created_at": "2026-04-29T21:52:00+03:00"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

#### POST /bookings

Create a new booking.

**Request Body:**

```json
{
  "client_phone": "+79161234567",
  "client_name": "Мария",
  "master_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "service_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "start_at": "2026-05-15T14:00:00+03:00",
  "comment": "По возможности у окна",
  "source": "phone"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_phone` | string | ✅ | Phone number in `+7...` format |
| `client_name` | string | ✅ | Client name |
| `master_id` | UUID | ✅ | Master ID |
| `service_id` | UUID | ✅ | Service ID |
| `start_at` | ISO 8601 | ✅ | Booking start date/time |
| `comment` | string | No | Client comment |
| `source` | string | No | `phone` (default), `telegram`, `admin` |

**Response `201 Created`:**

```json
{
  "booking_id": "3f5e8c2a-1b4d-4f7e-9a6c-8d3e2f1a0b5c",
  "status": "confirmed",
  "yclients_id": 98765,
  "summary": "Маникюр у Анны, 15 мая в 14:00, 1500 ₽"
}
```

**Error Responses:**

```json
// 409 Conflict — slot is already taken
{ "error": "SLOT_TAKEN", "message": "Время 14:00 уже занято" }

// 422 Unprocessable — service or master unavailable
{ "error": "SERVICE_UNAVAILABLE", "message": "Услуга временно недоступна" }
{ "error": "MASTER_UNAVAILABLE", "message": "Мастер не работает в это время" }
{ "error": "INVALID_TIME", "message": "Время не входит в рабочие часы" }
```

---

#### GET /bookings/{booking_id}

Get booking details.

**Response `200 OK`:**

```json
{
  "booking_id": "3f5e8c2a-1b4d-4f7e-9a6c-8d3e2f1a0b5c",
  "status": "confirmed",
  "client": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "Мария Иванова",
    "phone": "+79161234567"
  },
  "master": {
    "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "name": "Анна Петрова"
  },
  "service": {
    "name": "Маникюр",
    "price_rub": 1500.00,
    "duration_min": 60
  },
  "start_at": "2026-05-15T14:00:00+03:00",
  "end_at": "2026-05-15T15:00:00+03:00",
  "comment": null,
  "source": "phone",
  "yclients_id": 98765,
  "created_at": "2026-04-29T21:52:00+03:00",
  "updated_at": "2026-04-29T21:52:00+03:00",
  "history": [
    {
      "from_status": null,
      "to_status": "confirmed",
      "changed_by": "ai",
      "reason": null,
      "created_at": "2026-04-29T21:52:00+03:00"
    }
  ]
}
```

**Response `404 Not Found`:**

```json
{ "error": "BOOKING_NOT_FOUND", "message": "Booking not found" }
```

---

#### PATCH /bookings/{booking_id}

Modify an existing booking (reschedule, cancel, change service/master).

**Request Body:**

```json
// Reschedule
{
  "action": "reschedule",
  "start_at": "2026-05-16T10:00:00+03:00",
  "master_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "reason": "Клиент попросил перенести"
}

// Cancel
{
  "action": "cancel",
  "reason": "client_request",
  "comment": "Ппередумала"
}

// Change service
{
  "action": "update_service",
  "service_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
  "reason": "Клиент хочет другую услугу"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | ✅ | `reschedule`, `cancel`, `update_service`, `update_master` |
| `start_at` | ISO 8601 | For `reschedule` | New start time |
| `master_id` | UUID | For `reschedule` / `update_master` | New master |
| `service_id` | UUID | For `update_service` | New service |
| `reason` | string | For `cancel` | Cancellation reason: `client_request`, `no_show`, `other` |
| `comment` | string | No | Additional comment |

**Response `200 OK` (reschedule):**

```json
{
  "booking_id": "3f5e8c2a-1b4d-4f7e-9a6c-8d3e2f1a0b5c",
  "status": "confirmed",
  "old_start_at": "2026-05-15T14:00:00+03:00",
  "new_start_at": "2026-05-16T10:00:00+03:00",
  "summary": "Стрижка у Анны перенесена на 16 мая в 10:00"
}
```

**Response `200 OK` (cancel):**

```json
{
  "booking_id": "3f5e8c2a-1b4d-4f7e-9a6c-8d3e2f1a0b5c",
  "status": "cancelled",
  "cancelled_at": "2026-04-29T22:00:00+03:00",
  "penalty_info": null
}
```

**Error Responses:**

```json
// 409 Conflict — target slot is taken (reschedule)
{ "error": "SLOT_TAKEN", "message": "Новое время уже занято" }

// 422 — cancellation within 2-hour window
{ "error": "LATE_CANCEL", "message": "Отмена менее чем за 2 часа до начала", "penalty": true }
```

---

#### DELETE /bookings/{booking_id}

Cancel a booking (alternative to PATCH with `action: cancel`).

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `reason` | string | No | `client_request`, `no_show`, `other` (default: `client_request`) |

**Response `200 OK`:**

```json
{
  "booking_id": "3f5e8c2a-1b4d-4f7e-9a6c-8d3e2f1a0b5c",
  "status": "cancelled",
  "cancelled_at": "2026-04-29T22:00:00+03:00"
}
```

---

### Slots

#### GET /slots

Find available time slots for a specific date.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date` | YYYY-MM-DD | ✅ | Target date |
| `service_id` | UUID | No | Service ID (determines duration) |
| `master_id` | UUID | No | Filter by master (if omitted, all masters) |

**Response `200 OK`:**

```json
{
  "date": "2026-05-15",
  "slots": [
    {
      "start": "2026-05-15T14:00:00+03:00",
      "end": "2026-05-15T15:00:00+03:00",
      "master_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "master_name": "Анна Петрова"
    },
    {
      "start": "2026-05-15T16:00:00+03:00",
      "end": "2026-05-15T17:00:00+03:00",
      "master_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "master_name": "Анна Петрова"
    },
    {
      "start": "2026-05-15T14:00:00+03:00",
      "end": "2026-05-15T15:00:00+03:00",
      "master_id": "e5f6a7b8-c9d0-1234-efab-345678901234",
      "master_name": "Елена Соколова"
    }
  ]
}
```

**Empty Response:**

```json
{
  "date": "2026-05-15",
  "slots": []
}
```

---

### Clients

#### GET /clients/by-phone/{phone}

Look up a client by phone number. Used by the Engine to identify repeat callers.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `phone` | string | Phone number in `+7...` format (URL-encoded) |

**Response `200 OK`:**

```json
{
  "client": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "name": "Мария Иванова",
    "phone": "+79161234567",
    "total_visits": 5,
    "last_visit_at": "2026-03-15T14:00:00+03:00",
    "preferred_master_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "preferred_services": ["стрижка", "окрашивание"]
  },
  "last_booking": {
    "service": "Стрижка женская",
    "master": "Анна Петрова",
    "date": "2026-03-15"
  }
}
```

**Response `404 Not Found`:**

```json
{ "error": "CLIENT_NOT_FOUND", "message": "Клиент не найден" }
```

---

### Services & Masters

#### GET /services

List all services offered by the salon.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | No | Filter by category: `стрижки`, `окрашивание`, `маникюр`, `педикюр`, `уход` |
| `is_active` | bool | No | Filter by active status (default: `true`) |

**Response `200 OK`:**

```json
{
  "services": [
    {
      "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "name": "Стрижка женская",
      "description": "Стрижка любой сложности с укладкой",
      "duration_min": 60,
      "price_rub": 2500.00,
      "category": "стрижки",
      "is_active": true
    },
    {
      "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
      "name": "Маникюр классический",
      "description": "Обрезной маникюр с покрытием",
      "duration_min": 90,
      "price_rub": 1500.00,
      "category": "маникюр",
      "is_active": true
    }
  ]
}
```

---

#### GET /masters

List masters (employees).

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `service_id` | UUID | No | Filter masters who provide a specific service |
| `is_active` | bool | No | Filter by active status (default: `true`) |

**Response `200 OK`:**

```json
{
  "masters": [
    {
      "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "name": "Анна Петрова",
      "phone": "+79991234567",
      "specialization": "Стрижки, окрашивание",
      "is_active": true,
      "services": [
        {
          "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
          "name": "Стрижка женская"
        }
      ]
    }
  ]
}
```

---

### Business Info

#### GET /info

Get salon information (name, address, working hours, holidays).

**Response `200 OK`:**

```json
{
  "name": "Салон красоты Элегант",
  "address": "ул. Тверская, д. 15",
  "phone": "+74951234567",
  "work_hours": {
    "mon-fri": "09:00-21:00",
    "sat": "10:00-20:00",
    "sun": "10:00-18:00"
  },
  "next_holiday": "2026-05-11",
  "timezone": "Europe/Moscow",
  "description": "Салон красоты премиум-класса в центре Москвы"
}
```

---

### Escalation

#### POST /escalate

Escalate a call to a human (salon owner). This triggers a SIP transfer and sends a Telegram notification.

**Request Body:**

```json
{
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "reason": "complaint",
  "client_summary": "Клиентка недовольна ценой на окрашивание, просит поговорить с администратором"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `call_id` | UUID | ✅ | Call ID |
| `reason` | string | ✅ | `complaint`, `aggressive`, `complex_request`, `other` |
| `client_summary` | string | No | Brief context for the owner |

**Response `200 OK`:**

```json
{
  "action": "transfer",
  "forward_to": "+79991234567",
  "transfer_initiated": true
}
```

**Response `200 OK` (owner unavailable):**

```json
{
  "action": "task_created",
  "forward_to": null,
  "transfer_initiated": false,
  "message": "Administrator is unavailable. A task has been created to call back."
}
```

---

### Error Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing API key |
| `TENANT_INACTIVE` | 403 | Tenant is suspended or deleted |
| `TENANT_NOT_FOUND` | 404 | Tenant doesn't exist |
| `BOOKING_NOT_FOUND` | 404 | Booking not found |
| `CLIENT_NOT_FOUND` | 404 | Client not found |
| `SLOT_TAKEN` | 409 | Time slot is already occupied |
| `LATE_CANCEL` | 422 | Cancellation within 2-hour window |
| `SERVICE_UNAVAILABLE` | 422 | Service is temporarily unavailable |
| `MASTER_UNAVAILABLE` | 422 | Master doesn't work at this time |
| `INVALID_TIME` | 422 | Time is outside working hours |
| `RATE_LIMITED` | 429 | Rate limit exceeded (100 req/min per tenant) |

Error responses follow a consistent format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable description in Russian",
  "details": {}
}
```

---

## 2. Engine Service API

**Base URL:** `http://engine:8002`

---

### POST /process

Process a client utterance and get an AI response.

**Request Body:**

```json
{
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "tenant_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "text": "хочу записаться на стрижку на завтра",
  "is_final": true,
  "words": [
    {"text": "хочу", "start_sec": 0.5, "end_sec": 0.8, "confidence": 0.97},
    {"text": "записаться", "start_sec": 0.9, "end_sec": 1.3, "confidence": 0.95},
    {"text": "на", "start_sec": 1.4, "end_sec": 1.5, "confidence": 0.99},
    {"text": "стрижку", "start_sec": 1.6, "end_sec": 2.1, "confidence": 0.93},
    {"text": "на", "start_sec": 2.2, "end_sec": 2.3, "confidence": 0.99},
    {"text": "завтра", "start_sec": 2.4, "end_sec": 2.8, "confidence": 0.91}
  ]
}
```

**Response `200 OK`:**

```json
{
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "text": "На завтра, 15 мая, у нас есть свободное время в 14:00 и 16:00. Вам какое удобнее?",
  "tts_priority": true,
  "tool_calls": [
    {
      "tool": "find_slots",
      "args": {
        "service": "стрижка",
        "date": "2026-05-15",
        "master_name": null
      },
      "result": {
        "slots": [
          {"master": "Анна", "start": "2026-05-15T14:00:00+03:00", "end": "2026-05-15T15:00:00+03:00"},
          {"master": "Елена", "start": "2026-05-15T16:00:00+03:00", "end": "2026-05-15T17:00:00+03:00"}
        ]
      }
    }
  ],
  "dialog_state": {
    "turn": 2,
    "client_intent": "booking",
    "identified_client": {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Мария Иванова"
    }
  }
}
```

---

### POST /reset

Reset dialog state for a call (e.g., when the call ends or a new call starts).

**Request Body:**

```json
{
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "reason": "call_ended"
}
```

**Response `200 OK`:**

```json
{
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "status": "reset",
  "cleared_keys": ["session", "history", "context"]
}
```

---

### WebSocket /ws/dialog/{call_id}

Full-duplex WebSocket for real-time dialog with the Gateway.

**Gateway → Engine messages (client speech):**

```json
{
  "event": "client_speech",
  "call_id": "uuid",
  "tenant_id": "uuid",
  "text": "хочу записаться на маникюр на завтра",
  "is_final": true,
  "words": [{"text": "...", "start_sec": 0.3, "end_sec": 0.8, "confidence": 0.95}]
}
```

**Engine → Gateway messages (AI response):**

```json
{
  "event": "ai_response",
  "call_id": "uuid",
  "text": "На завтра, 15 мая, у нас есть свободное время в 14:00 и 16:00.",
  "tts_priority": true,
  "tool_calls": [...]
}
```

**Engine → Gateway messages (action result):**

```json
{
  "event": "action",
  "call_id": "uuid",
  "action": "create_booking",
  "result": {
    "booking_id": "uuid",
    "status": "confirmed",
    "summary": "Маникюр у Анны, 15 мая в 14:00, 1500 ₽"
  }
}
```

**Interrupt handling (Gateway → Engine):**

```json
{
  "event": "interrupt",
  "call_id": "uuid",
  "interrupted_text": "а можно в пятницу?"
}
```

---

## 3. Speech Service API

**Base URL:** `ws://speech:8001`

---

### WebSocket /ws/asr/{call_id}

Real-time ASR (Automatic Speech Recognition) stream. Client sends binary audio chunks, receives JSON transcription frames.

**Client → Server:**

```json
// Frame 1 (JSON text start)
{
  "event": "start",
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "tenant_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "sample_rate": 8000,
  "format": "opus",
  "language": "ru-RU",
  "custom_vocabulary": ["стрижка", "окрашивание", "маникюр", "педикюр", "биозавивка", "укладка"]
}

// Frame 2..N (binary audio chunks)
[binary: opus audio frame]

// Frame N (JSON text end)
{
  "event": "end"
}
```

**Server → Client:**

```json
// Intermediate (partial) transcript
{
  "event": "transcript",
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "text": "здравствуйте я хотела бы",
  "is_final": false,
  "confidence": 0.89
}

// Final transcript
{
  "event": "transcript",
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "text": "здравствуйте я хотела бы записаться на стрижку",
  "is_final": true,
  "confidence": 0.95,
  "words": [
    {"text": "здравствуйте", "start_sec": 0.3, "end_sec": 1.1, "confidence": 0.98},
    {"text": "стрижку", "start_sec": 4.2, "end_sec": 4.8, "confidence": 0.91}
  ]
}

// Error
{
  "event": "error",
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "code": "ASR_TIMEOUT",
  "message": "No speech detected for 30 seconds"
}
```

---

### WebSocket /ws/vad/{call_id}

Real-time VAD (Voice Activity Detection) stream. Client sends binary audio chunks, receives speech start/end events.

**Client → Server (JSON start):**

```json
{
  "event": "start",
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "sample_rate": 8000,
  "format": "opus",
  "vad_level": 2
}
```

**Server → Client (events):**

```json
// Speech detected
{
  "event": "speech_start",
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "time_sec": 3.2
}

// Speech ended
{
  "event": "speech_end",
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "time_sec": 7.8,
  "duration_sec": 4.6
}

// Silence timeout
{
  "event": "silence_timeout",
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "time_sec": 35.0
}
```

---

### gRPC TTSService

**Proto definition:**

```protobuf
service TTSService {
  rpc Synthesize(stream TTSRequest) returns (stream TTSResponse);
}

message TTSRequest {
  string call_id = 1;
  string text = 2;
  string voice = 3;        // "alena" | "ermil"
  int32 sample_rate = 4;   // 8000
  bool streaming_mode = 5;
}

message TTSResponse {
  string call_id = 1;
  bytes audio_chunk = 2;
  int32 chunk_sequence = 3;
  bool is_final = 4;
  string text_spoken = 5;
}
```

**Example flow:**

```python
import grpc
import tts_pb2, tts_pb2_grpc

channel = grpc.insecure_channel("speech:8001")
stub = tts_pb2_grpc.TTSServiceStub(channel)

def request_generator():
    yield tts_pb2.TTSRequest(
        call_id="f7a8b9c0-d1e2-3456-fabc-678901234567",
        text="Здравствуйте! Чем могу помочь?",
        voice="alena",
        sample_rate=8000,
        streaming_mode=True,
    )

for response in stub.Synthesize(request_generator()):
    if response.audio_chunk:
        # Send audio chunk to SIP client
        ...
    if response.is_final:
        break
```

---

## 4. Gateway API

**Base URL:** `http://gateway:8000`

---

### POST /api/v1/calls/inbound

Handle an inbound call notification (webhook from Sipuni).

**Request Body (Sipuni webhook format):**

```json
{
  "call_id": "sipuni-session-12345",
  "did": "+74951234567",
  "caller_number": "+79161234567",
  "caller_name": "Мария Иванова",
  "event": "call_start"
}
```

**Response `200 OK`:**

```json
{
  "status": "accepted",
  "internal_call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "tenant_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### GET /api/v1/calls/{call_id}/status

Get the current status of a call.

**Response `200 OK`:**

```json
{
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "status": "in_progress",
  "pipeline_state": "speaking",
  "duration_sec": 42,
  "tenant_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### POST /api/v1/calls/{call_id}/transfer

Initiate a SIP call transfer (used for escalation).

**Request Body:**

```json
{
  "target_number": "+79991234567",
  "reason": "escalation"
}
```

**Response `200 OK`:**

```json
{
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "status": "transferring",
  "target": "+79991234567"
}
```

---

### POST /api/v1/calls/{call_id}/hangup

Forcefully end a call.

**Response `200 OK`:**

```json
{
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "status": "completed",
  "duration_sec": 142
}
```

---

## 5. Admin Panel API

**Base URL:** `http://admin:8004/api/admin/v1`

**Auth:** JWT Bearer token (obtained via login form).

---

### Tenants

```http
GET    /tenants                    # List all tenants (superadmin)
POST   /tenants                    # Create a new tenant
GET    /tenants/{id}               # Get tenant info
PATCH  /tenants/{id}               # Update tenant
```

### Statistics

```http
GET    /tenants/{id}/stats/calls        # Call statistics (daily/weekly/monthly)
GET    /tenants/{id}/stats/bookings     # Booking statistics
GET    /tenants/{id}/stats/escalations  # Escalation statistics
```

**Response example (`/stats/calls`):**

```json
{
  "period": "2026-05-01..2026-05-15",
  "total_calls": 42,
  "answered": 40,
  "missed": 2,
  "avg_duration_sec": 85,
  "bookings_created": 18,
  "escalations": 3,
  "daily_breakdown": [
    {"date": "2026-05-15", "calls": 8, "bookings": 5},
    {"date": "2026-05-14", "calls": 6, "bookings": 3}
  ]
}
```

### Calls

```http
GET    /tenants/{id}/calls              # Call history (paginated)
GET    /tenants/{id}/calls/{call_id}    # Call details with transcript + audio URL
```

**Response (`/calls/{call_id}`):**

```json
{
  "call_id": "f7a8b9c0-d1e2-3456-fabc-678901234567",
  "caller_phone": "+79161234567",
  "client_name": "Мария Иванова",
  "status": "completed",
  "result": "booking_created",
  "duration_sec": 142,
  "audio_url": "https://minio.internal/allo-audio/tenant-uuid/2026-05-15/call-uuid.opus?expires=3600",
  "transcript": [
    {"speaker": "ai", "text": "Салон красоты «Элегант», здравствуйте!", "time_sec": 0.0},
    {"speaker": "client", "text": "Здравствуйте, хочу записаться на стрижку", "time_sec": 3.2},
    {"speaker": "ai", "text": "Конечно! На какое время вам удобно?", "time_sec": 5.1},
    {"speaker": "client", "text": "На завтра после обеда", "time_sec": 7.8},
    {"speaker": "ai", "text": "Завтра есть свободное время в 14:00 и 16:00. Вам какое удобнее?", "time_sec": 10.0}
  ],
  "booking_result": {
    "id": "3f5e8c2a-1b4d-4f7e-9a6c-8d3e2f1a0b5c",
    "service": "Стрижка женская",
    "master": "Анна Петрова",
    "start_at": "2026-05-16T14:00:00+03:00"
  },
  "created_at": "2026-05-15T14:32:00+03:00"
}
```

### Prompt Profile

```http
GET    /tenants/{id}/prompt-profile      # Get current prompt profile with blocks
PUT    /tenants/{id}/prompt-profile      # Update prompt blocks
```

### SIP Settings

```http
GET    /tenants/{id}/sip-settings        # Get SIP configuration
PUT    /tenants/{id}/sip-settings        # Update SIP configuration
```

### Test Call

```http
POST   /tenants/{id}/test-call           # Initiate a test call to verify setup
```
