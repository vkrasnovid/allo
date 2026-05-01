# CODE REVIEW — Алло (TASK-026) Voice AI Secretary

**Date:** 2026-05-01  
**Reviewer:** Code Reviewer (subagent)  
**Scope:** Full codebase audit — 7 services + shared libs + admin panel + OpenClaw plugins  

---

## Overall Verdict: CHANGES_REQUESTED

```
APPROVED:     ❌ (blocked by critical issues)
P0 (critical): 3
P1 (major):    7
P2 (minor):    8
```

The project has an excellent architectural foundation but has **two concrete critical issues** that prevent the real-time voice pipeline from functioning, and several security/architectural gaps that must be resolved before deployment.

---

## Scoring

| Category | Score | Notes |
|----------|:-----:|-------|
| **Security** | **5.5/10** | ❌ No ForeignKey constraints, missing TenantMiddleware on engine, no encryption at rest |
| **Architecture** | **6/10** | ⚠️ Protocol mismatch between gateway↔engine WS, LLM init conditionally works |
| **Code Quality** | **7/10** | ✅ Good typing, Pydantic everywhere, clean monorepo |
| **Integrations** | **6/10** | ⚠️ YCliest adapter is stub, Celery stubs, Sipuni/SpeechKit API wrappers OK |
| **Test Coverage** | **5/10** | ❌ Zero gateway/speech WS tests, no integration tests |
| **Overall** | **5.9/10** | |

---

## P0 — Critical Issues (Blocking)

### P0-1. WebSocket protocol mismatch: Gateway ↔ Engine message schemas are incompatible

**Severity:** BLOCKING  
**Files:** `gateway/src/main.py`, `engine/src/main.py`

**What:** The gateway's `audio_relay()` WebSocket handler opens a connection to `ws://engine:8002/ws/dialog/{session_id}` (engine *does* have this endpoint — contrary to previous review). However, the two sides speak **completely different message protocols**.

Gateway sends these message types to engine:
```python
# gateway/src/main.py lines ~200-240
{"type": "call_start", "session_id": "...", "call_id": "...", "tenant_id": "...", ...}
{"type": "system_message", "text": "...", "tts_priority": True}
{"type": "client_speech", "text": "...", "is_final": True, ...}
{"type": "vad_event", "event": "speech_start|speech_end|silence_timeout"}
{"type": "interrupt_signal"}
```

Engine's WebSocket handler expects:
```python
# engine/src/main.py — dialog_websocket()
{"type": "process", "tenant_id": "...", "text": "...", "client_phone": "..."}
{"type": "reset", "tenant_id": "..."}
{"type": "tool_call_result", "tenant_id": "...", "tool_name": "...", "args": {...}, "result": {...}}
```

The gateway expects engine responses with `ai_response`, `action`, `error` types:
```python
# gateway/src/main.py — _engine_to_client()
if rtype == "ai_response": ...
elif rtype == "action": ...
elif rtype == "error": ...
```

The engine instead sends:
```python
{"type": "response", "data": {...}}
{"type": "error", "message": "..."}
```

**Effect:** Every message from the gateway hits the `Unknown message type: {msg_type}` branch in the engine. The gateway's `_engine_to_client()` receives these error responses instead of `ai_response`. The audio pipeline collapses immediately on every call. All inbound calls would be forwarded to the fallback number (`_forward_to_owner`).

**Fix:** Either:
- (a) Update `engine/src/main.py` dialog_websocket to handle `call_start`, `client_speech`, `vad_event`, `system_message`, `interrupt_signal` types and respond with `ai_response`, `action`, `error`
- (b) OR drop the WebSocket approach and make gateway call `POST /api/engine/message` REST endpoint — but this would lose the streaming/real-time nature

Recommended fix (a) structure:
```python
@app.websocket("/ws/dialog/{call_id}")
async def dialog_websocket(ws: WebSocket, call_id: str):
    ...
    async def _handle_call_start(msg):
        # Initialize session, store call context
        ...
    async def _handle_client_speech(msg):
        # Process speech via dialog manager, stream response back
        result = await dialog_manager.process_user_message(...)
        if result["reply"]:
            await ws.send_json({"type": "ai_response", "text": result["reply"]})
    async def _handle_vad_event(msg):
        if msg["event"] == "speech_start":
            await ws.send_json({"type": "interrupt_signal"})
    ...
```

---

### P0-2. Missing `and_` SQLAlchemy import in routes.py

**Severity:** BLOCKING  
**File:** `booking/src/api/routes.py` line 10

**What:** `from sqlalchemy import select, func, delete` — `and_` is not imported but is used in `get_client_by_phone()`:
```python
.outerjoin(BookingORM, and_(
    BookingORM.client_id == ClientORM.id,
    BookingORM.status == "completed",
))
```

**Effect:** `GET /tenants/{id}/clients/by-phone/{phone}` crashes with `NameError: name 'and_' is not defined`. This is the endpoint used to look up returning clients — a core UX path.

**Fix:** Add `and_` to the SQLAlchemy import line:
```python
from sqlalchemy import select, func, delete, and_
```

---

### P0-3. Gateway and engine WebSocket protocols don't send/receive session initialization properly

**Severity:** BLOCKING  
**Files:** `gateway/src/main.py` lines 175-195, `engine/src/main.py`

**What:** Even after fixing P0-1, the gateway sends `{"type": "call_start"}` with session metadata before any audio flows. The gateway's `_engine_to_client()` concurrently reads for `ai_response` messages. But the engine was designed as a request-response WS (client sends `process` → server sends `response`), not a bidirectional conversation channel.

Additionally, the gateway fails to forward the `call_start` data as `tenant_id` to the engine's dialog manager — the WS handler in engine requires `tenant_id` in every message but the gateway's `call_start` and `client_speech` messages _do_ include it.

**Fix:** Implement proper bidirectional WS protocol with message routing by type in the engine (see P0-1 fix recommendation).

---

## P1 — Major Issues (Should Fix Before MVP)

### P1-1. All ORM models lack ForeignKey constraints

**Severity:** MAJOR  
**Files:** All models in `booking/src/models/*.py`

**What:** Despite detailed SQL schema in ARCHITECTURE.md specifying `REFERENCES tenants(id) ON DELETE CASCADE`, none of the ORM models define `ForeignKey` columns. Only SQLAlchemy `relationship()` directives exist, which do **not** enforce referential integrity at the database level.

Affected tables:
- `BookingORM.tenant_id`, `.client_id`, `.master_id`, `.service_id` — no FK
- `CallORM.tenant_id`, `.client_id` — no FK
- `ClientORM.tenant_id` — no FK
- `ServiceORM.tenant_id` — no FK
- `MasterORM.tenant_id` — no FK
- `BookingHistoryORM.booking_id` — no FK
- `SipSettingsORM.tenant_id` — no FK

**Effect:** Orphaned records, no cascade deletes. If a tenant is deleted, all their data stays in the DB as garbage. No DB-level protection against referential corruption.

**Fix:** Add `ForeignKey` to all `mapped_column` definitions:
```python
from sqlalchemy import ForeignKey

# In each model:
tenant_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("tenants.id", ondelete="CASCADE"),
    nullable=False, index=True,
)
```

---

### P1-2. Docker Compose YAML anchor merge syntax is broken

**Severity:** MAJOR  
**File:** `docker-compose.yml`

**What:** Services use `<<: [*default-restart, *default-logging]` — a list-based YAML merge. The `logging` key is a structured YAML key, and merging it as a flat anchor list causes `driver` and `options` to become top-level service properties instead of nesting under `logging:`.

```yaml
x-logging: &default-logging
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"

x-restart: &default-restart
  restart: unless-stopped

# Broken:
services:
  postgres:
    <<: [*default-restart, *default-logging]  # driver leaks to service root
```

**Effect:** `docker compose config` fails to validate. In some versions the keys silently leak. The `logging` block is not properly applied, so containers use default Docker logging (json-file without rotation limits), which will fill disk.

**Fix:** Split into two merge sources:
```yaml
postgres:
  <<: *default-restart
  logging: *default-logging
```

---

### P1-3. Engine lacks TenantMiddleware — no tenant validation

**Severity:** MAJOR  
**File:** `engine/src/main.py`

**What:** The booking service's router automatically validates tenant existence/status via `await _get_tenant(db, tenant_id)` in each endpoint. The engine has **no such validation**. Any request with any `tenant_id` (including fake or deleted tenants) is processed normally.

**Effect:** Malformed or malicious requests can trigger tool execution against non-existent tenants. Could lead to data inconsistency (Redis state stored for phantom tenants) or subtle bugs.

**Fix:** Add tenant validation in `DialogManager.process_user_message()`:
```python
async def process_user_message(self, tenant_id, call_id, text, ...):
    # Validate tenant exists
    if not await self.tools.booking_client.validate_tenant(tenant_id):
        return {"error": "TENANT_NOT_FOUND", "reply": "Извините, произошла ошибка"}
    ...
```

---

### P1-4. `sip_password` — declared ENCRYPTED in schema but stored plaintext (or missing)

**Severity:** MAJOR  
**File:** `booking/src/models/sip.py`, `shared/security/__init__.py`

**What:** ARCHITECTURE.md §8.2 specifies Fernet encryption for `sip_password VARCHAR(255) ENCRYPTED`. The ORM model `SipSettingsORM` defines `sip_password: Mapped[str | None]` with no encryption at the ORM layer. The `FieldEncryption` class exists in `shared/security/` but is **never used** anywhere in the codebase.

**Effect:** Any SIP password stored in the database would be in plaintext. If someone gains DB access, they get the SIP credentials.

**Fix:** Either:
- (a) Add `before_insert` / `before_update` listener on `SipSettingsORM` to auto-encrypt via `FieldEncryption`
- (b) Or make encryption explicit in the seed/admin API where the password is stored

---

### P1-5. Celery notification tasks are stubs — no real notification sending

**Severity:** MAJOR  
**Files:** `notifications/src/tasks.py`, `notifications/src/celery_app.py`

**What:** The architecture specifies Celery-based SMS reminders, audio cleanup, and YClients sync. The `tasks.py` file has:
- `send_reminders()` — checks booking service health but sends zero actual SMS
- `send_single_sms()` — works but is never called by anything
- `cleanup_sessions()` — placeholder that logs and returns

**Effect:** SMS reminders, audio cleanup, and background YClients sync don't work.

**Fix:** Implement `send_reminders` to query `scheduled_notifications` table, get upcoming bookings, and actually call `sms_provider.send_sms()`.

---

### P1-6. Gateway service has no rate limiting

**Severity:** MAJOR  
**File:** `gateway/src/main.py`

**What:** ARCHITECTURE.md §8.1 specifies rate limiting at 100 req/min per tenant. The gateway has no rate limiting middleware. The booking service also lacks rate limiting.

**Effect:** An attacker (or misconfigured Sipuni) can flood the inbound call endpoint, creating unlimited `ActiveCall` objects and triggering OOM.

**Fix:** Add `slowapi` or custom Redis-backed rate limiter on `POST /api/v1/calls/inbound` and other gateway endpoints.

---

### P1-7. No S3/MinIO integration for call recordings

**Severity:** MAJOR  
**Files:** `gateway/src/main.py`, `speech/src/main.py`, `docker-compose.yml`

**What:** ARCHITECTURE.md specifies S3/MinIO for audio storage (90-day retention). The `docker-compose.yml` defines a MinIO container with credentials. BUT:
- The gateway never saves audio to S3
- There's no `minio/` or `s3/` module in any service
- The `audio_key` field in `CallORM` is never populated
- No audio cleanup job exists

**Effect:** Call recordings are never persisted. Can't review past calls, no audit trail.

**Fix:** Implement audio capture in `gateway/src/main.py` audio relay — buffer the full conversation and upload to MinIO when the call ends (or periodically).

---

## P2 — Minor Issues (Should Fix)

### P2-1. Energy-based VAD instead of specified Silero VAD

**File:** `speech/src/main.py`

ARCHITECTURE.md specifies Silero VAD (neural network). Implementation uses simple RMS threshold (`VAD_RMS_THRESHOLD = 300.0`). On 8 kHz telephone audio, this is unreliable — background noise, breathing, line noise all produce RMS > 300. Silero VAD is significantly more robust.

**Priority:** P2 — RMS may work well enough for MVP in quiet environments, but will false-positive in noisy settings.

---

### P2-2. Gateway WS `asyncio.gather` — partial failure doesn't clean up all connections

**File:** `gateway/src/main.py` lines 257-292

```python
await asyncio.gather(
    _client_to_speech(),
    _asr_to_engine(),
    _vad_to_engine(),
    _engine_to_client(),
)
```

If one task fails, the other three keep running until the `finally` block. However, the `stop` event may not be set in time — if `_engine_to_client()` fails (which it will with current protocol mismatch), the ASR and VAD connections continue consuming resources. The `finally` block does attempt to close all WS connections.

**Fix:** Use `asyncio.gather(..., return_exceptions=True)` and check results to ensure immediate full cleanup.

---

### P2-3. `HallucinationLog.get_stats()` returns empty `by_tool`

**File:** `engine/src/dialog/guard.py`

`log()` records per-tool events in `self.events`, but `get_stats()` returns `"by_tool": {}` — it never aggregates by tool name.

**Fix:** Track tool-level counts:
```python
def log(self, tool_name: str, params: dict, reason: str):
    self.events.append({...})
    self.by_tool.setdefault(tool_name, 0)
    self.by_tool[tool_name] += 1
```

---

### P2-4. `db.flush()` called redundantly in booking creation

**File:** `booking/src/api/routes.py`

`_get_or_create_client()` calls `await db.flush()` internally (to get `client.id`). The `create_booking()` route calls `await db.flush()` again after adding the booking. The second flush is redundant.

---

### P2-5. Redis connection pooling not configured

**File:** `engine/src/state/redis_manager.py`

`redis.from_url(REDIS_URL)` creates a single connection. Under load (e.g., 20+ concurrent calls), `redis-py` queues requests on this single connection. The architecture implies Redis-backed state for many concurrent calls.

**Fix:** Use connection pool:
```python
self.redis = await aioredis.from_url(REDIS_URL, max_connections=20, ...)
```

---

### P2-6. `__import__("datetime")` anti-pattern

**File:** `booking/src/api/routes.py`

Multiple uses of `__import__("datetime").timedelta()` instead of `from datetime import timedelta` at the top of the file. Fragile, hard to maintain, and obscures intent.

---

### P2-7. No WebSocket tests for speech service or gateway

**Files:** `speech/tests/`, `gateway/tests/` — don't exist as test directories

The most latency-sensitive components (real-time ASR, VAD, TTS) have zero tests. The gateway's `audio_relay` WebSocket handler is untested.

**Fix:** Add `pytest` tests using `httpx` WebSocket test transport.

---

### P2-8. `update_booking` PATCH uses `action` field for "cancel" — should use DELETE

**File:** `booking/src/api/routes.py`

`BookingUpdateRequest` allows `action = "cancel"` via PATCH. There's already a dedicated `DELETE /bookings/{id}` endpoint. Having two ways to cancel is confusing and breaks REST semantics.

---

## Integration-Specific Checks

### Sipuni API (`gateway/src/main.py`)
- ✅ HMAC-SHA256 verification for webhooks
- ✅ Exponential backoff retry (3 retries)
- ✅ Fallback to `ALLO_FALLBACK_DIRECT` when tenant not resolved
- ✅ Proper error logging with `_mask_phone()` (PII-safe)

### Yandex SpeechKit (`speech/src/main.py`)
- ✅ API-Key header via `_yc_headers()`
- ✅ Retry with backoff for both ASR and TTS
- ✅ Audio format matched between ASR/TTS (LPCM, 8kHz)
- ⚠️ Hardcoded `topic: "general"` — could benefit from `"maps"` (for addresses) or custom model for beauty salon domain

### YClients Adapter (`booking/src/yclients/adapter.py`)
- ⚠️ **Stub only** — `is_available()` always returns `False` in the stub
- ⚠️ Lacks actual HTTP integration with YClients API
- ⚠️ Lacks auth token refresh logic

### Telegram Bot (`notifications/src/telegram/bot.py`)
- ✅ Anti-spam (30s cooldown per user — in-memory, lost on restart)
- ✅ Inline keyboards with proper callback routing
- ✅ Markdown formatting in messages
- ⚠️ All data fetching functions are stubs (`_fetch_bookings_for_today`, `_fetch_today_stats`)
- ⚠️ No webhook mode configured (uses polling)

### Telegram Plugin (`openclaw-plugins/telegram-bot/src/index.ts`)
- ✅ Proper `fetch`-based API calls
- ✅ Fallback when `TELEGRAM_BOT_TOKEN` not set
- ⚠️ No retry on network errors
- ⚠️ No HMAC verification for incoming updates (polling mode, but still)

---

## Architecture Compliance

| Architecture Decision | Status | Notes |
|----------------------|--------|-------|
| 5-layer isolation | ✅ Implemented | Clear service boundaries |
| PostgreSQL 15 | ✅ | asyncpg + SQLAlchemy 2 |
| Redis for state | ✅ | Keys with `tenant_id` prefix + TTL |
| Pydantic v2 contracts | ✅ | Between all layers |
| Multi-tenant `tenant_id` | ✅ | On all tables + Redis keys |
| RLS policies | ❌ Not implemented | Architecture specifies PostgreSQL RLS policy — not created |
| WS protocol spec | ❌ Mismatch | See P0-1 |
| Silero VAD | ❌ | RMS energy-based (cheaper but inferior) |
| S3 audio storage | ❌ Not implemented | MinIO defined but no upload code |
| Fernet encryption | ⚠️ Defined but unused | `FieldEncryption` class exists, never instantiated |
| Celery background tasks | ⚠️ Stubs | Task functions exist but bodies are stubbed |
| Rate limiting | ❌ Not implemented | Architecture specifies but absent |
| JWT auth for admin | ⚠️ Not implemented | Architecture specifies but admin uses no-auth mock data |
| 9 tools in registry | ✅ | Matches §4.4 specification |
| OpenClaw as LLM proxy | ⚠️ Partial | Client defined but conditionally initialized |
| Graceful degradation matrix | ⚠️ Partially | Some circuit breakers defined, none wired |

---

## Existing CODE_REVIEW.md — Corrections

The previous review (2026-04-30) had several inaccuracies:

1. **"C1 — Engine WebSocket endpoint missing"** — INCORRECT. The endpoint `/ws/dialog/{call_id}` **does exist** at `engine/src/main.py`. The real issue is **protocol incompatibility** (see P0-1 above).

2. **"C2 — LLM client never initialized"** — PARTIALLY INCORRECT. The LLM client **is initialized** when `OPENCLAIM_API_KEY` env var is truthy (which it is in docker-compose defaults: `OPENCLAW_API_KEY=-test_openclaw_key`). The real concern is that it silently falls back to stub mode in dev environments without the env var.

3. **"M1 — Docker Compose YAML anchor merge bug"** — CONFIRMED. Fixed in this review.

---

## Summary

```
STATUS: CHANGES_REQUESTED

P0 (blocking): 3
  - P0-1: WebSocket protocol mismatch (gateway ↔ engine)
  - P0-2: Missing `and_` import (crash on client lookup)
  - P0-3: Session init and protocol flow incomplete

P1 (major): 7
  - P1-1: Missing ForeignKey constraints on all ORM models
  - P1-2: Docker Compose merge syntax broken
  - P1-3: Engine lacks tenant validation
  - P1-4: SIP passwords stored without encryption
  - P1-5: Celery notification tasks are stubs
  - P1-6: No rate limiting on gateway
  - P1-7: No S3/MinIO audio storage integration

P2 (minor): 8
  - P2-1: RMS VAD instead of Silero VAD
  - P2-2: WS gather partial failure cleanup
  - P2-3: HallucinationLog by-tool stats empty
  - P2-4: Redundant db.flush()
  - P2-5: No Redis connection pool
  - P2-6: __import__ anti-pattern
  - P2-7: No WebSocket tests for speech/gateway
  - P2-8: Dual cancel semantics (PATCH + DELETE)
```

**Bottom line:** The codebase structure, typing, separation of concerns, and documentation are excellent. The architectural design is sound. However, two critical issues (WS protocol mismatch + missing import) and several missing security/privacy implementations prevent MVP deployment.

**Estimated fix effort:**
- P0 fixes: ~2-4 hours (WS protocol bridge + missing import)
- P1 fixes: ~4-6 hours (FK constraints, encryption, Docker fix, rate limiting, tenant validation)
- P2 fixes: ~3-5 hours (VAD tuning, logging fixes, test coverage, Redis pool)
- **Total: ~9-15 hours**
