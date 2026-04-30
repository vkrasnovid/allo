# CODE REVIEW — Алло (TASK-026) Voice AI Secretary

**Date:** 2026-04-30  
**Reviewer:** Code Reviewer (subagent)  
**Scope:** Full codebase audit — all 7 services + shared libraries + admin panel + OpenClaw plugins  

---

## Overall Verdict: CHANGES_REQUESTED

Two critical issues (non-functional voice pipeline entry points + missing LLM client initialization) prevent the core architecture from working end-to-end. Four major issues with varying severity. Once resolved, the codebase is structurally sound for MVP.

| Category | Score | Weight |
|----------|:-----:|:------:|
| Code Quality | 6/10 | ⚠️ |
| Architecture Compliance | 5/10 | ❌ |
| Security | 6/10 | ⚠️ |
| Error Handling | 7/10 | ✅ |
| Testing | 7/10 | ✅ |
| Performance | 5/10 | ⚠️ |
| API Design | 7/10 | ✅ |
| **Total** | **43/70** | |

---

## Score Breakdown

### 1. Code Quality — 6/10

**Good:**
- Full type hints across all Python and TypeScript files
- Pydantic v2 models used consistently for all schemas
- Clean separation of concerns across the monorepo structure
- Good naming conventions (snake_case Python, camelCase TS, descriptive names)
- Dockerfiles are syntactically valid

**Issues:**

- **[BUG] Missing `and_` import in routes.py** — `booking/src/api/routes.py` uses `and_()` from SQLAlchemy in `get_client_by_phone` (line ~293) but never imports it.
  ```python
  # Current import line:
  from sqlalchemy import select, func, delete
  # Should be:
  from sqlalchemy import select, func, delete, and_
  ```
  **Effect:** Runtime `NameError` when hitting `GET /tenants/{id}/clients/by-phone/{phone}`.

- **[BUG] LLM client never initialized** — `engine/src/main.py` line 28:
  ```python
  dialog_manager = DialogManager(
      state_manager=state_manager,
      tool_executor=tool_executor,
      llm_client=None,  # NEVER INITIALIZED
  )
  ```
  The `llm_client` parameter stays `None`. In `dialog/manager.py:process_user_message()`:
  ```python
  if self.llm:
      # Use LLM  ← NEVER REACHED
      ...
  else:
      # No LLM — return raw context (for testing)
      result["reply"] = "[NO LLM] Dialog manager running without LLM client"
  ```
  **Effect:** The engine always returns a stub message. No actual LLM inference happens.

- **[BUG] `hallucination_log.get_stats()` returns empty `by_tool`** — `HallucinationLog.log()` appends to `self.events` but `get_stats()` counts `"by_tool": {}` — it never actually populates the per-tool breakdown.

- **`__import__` abuse** — `booking/src/api/routes.py` uses `__import__("datetime").timedelta(...)` instead of a clean `from datetime import timedelta` at the top. This is fragile and anti-idiomatic.

- **`db.flush()` called twice in create_booking flow** — Once inside `_get_or_create_client()` and once after booking creation. Not harmful but redundant.

---

### 2. Architecture Compliance — 5/10

**Good:**
- Directory structure exactly matches ARCHITECTURE.md §1.3
- All 15 ORM models present (exceeds 14 minimum)
- 9 tools in `TOOL_REGISTRY` match §4.4
- Service boundaries largely respected
- Multi-tenant `tenant_id` pattern on all primary tables

**Issues:**

- **[CRITICAL] Engine missing WebSocket endpoint** — ARCHITECTURE.md §3.3 explicitly defines `ws://engine:8002/ws/dialog/{call_id}` with specific event schemas (`client_speech`, `ai_response`, `action`). The engine only implements REST endpoints (`POST /api/engine/message`). The gateway's `audio_relay` WebSocket connects to:
  ```python
  engine_url = f"{ENGINE_WS_URL}/{session_id}"  # ws://engine:8002/ws/dialog/{session_id}
  ```
  **Effect:** The entire real-time voice pipeline will disconnect immediately — gateway can't relay audio to engine, ASR output never reaches dialog manager, TTS output never reaches client.

- **[CRITICAL] Voice pipeline cannot function without engine WS** — The gateway's `_engine_to_client()` coroutine waits for engine WebSocket messages. Since that endpoint doesn't exist, the `asyncio.gather` in audio relay will fail immediately. The fallback `_forward_to_owner` will trigger, forwarding all calls to the salon owner — making the AI secretary non-functional.

- **[MAJOR] OpenClaw integration not wired** — Architecture §10 describes OpenClaw as LLM proxy and tool router. `engine/src/llm/__init__.py` defines `OpenClawLLMClient` but it's never instantiated in `engine/src/main.py`. The `OPENCLAW_API_URL` and `OPENCLAW_API_KEY` env vars exist in docker-compose but nothing uses them.

- **[MAJOR] Silero VAD vs energy-based VAD** — ARCHITECTURE.md specifies Silero VAD (a neural network model). The speech service implements a simple energy-based RMS threshold VAD. Silero is significantly more accurate at detecting speech/noise boundaries, especially on telephone-grade audio (8 kHz). The current implementation may produce false positives/negatives in real-world conditions.

- **[MINOR] Celery tasks not implemented** — Architecture §9.3 defines Celery tasks (reminders, cleanup, sync) but `notifications/src/tasks.py` is a stub. The `celery_app.py` exists but the actual task logic is missing.

---

### 3. Security — 6/10

**Good:**
- No hardcoded secrets or API keys in source code
- `FieldEncryption` class for sensitive DB fields (SIP passwords, YClients tokens)
- `.env.example` covers all required variables
- Pydantic pattern validation on phone numbers, IDs
- TenantMiddleware in booking service

**Issues:**

- **[MAJOR] Missing ForeignKey constraints on ORM models** — Multiple models lack proper foreign keys, meaning no database-level referential integrity:
  - `BookingORM.tenant_id` (no FK → tenants.id)
  - `BookingORM.client_id` (no FK → clients.id)
  - `BookingORM.master_id` (no FK → masters.id)
  - `BookingORM.service_id` (no FK → services.id)
  - `CallORM.tenant_id` (no FK → tenants.id)
  - `BookingHistoryORM.booking_id` (no FK → bookings.id)
  - etc.
  
  **Effect:** Deletes can orphan records. `ON DELETE CASCADE` specified in SQL schema but not enforced at the ORM/Database level.

- **[MAJOR] Engine lacks TenantMiddleware** — Confirmed by QA report. Engine has no middleware to validate tenant existence or status. A malformed request with a fake tenant_id would pass through.

- **[BUG] `sip_password` field storage** — Architecture §8.2 specifies `sip_password VARCHAR(255) ENCRYPTED` stored via `FieldEncryption`. The ORM model (`SipSettingsORM`) doesn't appear to store this field at all, and if it does, it's not encrypted. Sensitive credentials stored in plaintext.

- **[P3] Redis password hardcoded in some URLs** — In docker-compose fallback:
  ```yaml
  REDIS_URL: redis://:${REDIS_PASSWORD:-allo_redis_pass}@redis:6379/0
  ```
  Default password `allo_redis_pass` is hardcoded. Fine for dev but risky for production.

---

### 4. Error Handling — 7/10

**Good:**
- Graceful degradation matrix in architecture is well-thought-out
- `retry_async` utility with exponential backoff
- Circuit breaker pattern exists (even if not wired into services)
- Structured error responses (`{"error": "CODE", "message": "..."}`)
- Tool executor catches HTTP errors and wraps them gracefully

**Issues:**

- **[BUG] `asyncio.gather` partial failure in gateway** — `gateway/src/main.py` `audio_relay()` uses:
  ```python
  await asyncio.gather(
      _client_to_speech(),
      _asr_to_engine(),
      _vad_to_engine(),
      _engine_to_client(),
  )
  ```
  If one task fails, the others keep running with no cleanup. The `stop` event is set by individual tasks on error, but not by all paths. If `_engine_to_client()` fails (which it will, since WS endpoint doesn't exist), the `except Exception` in the outer try block handles it — but the individual WS connections may not be properly closed.

- **[MAJOR] Engine runs without LLM with no error signal** — When `llm_client=None`, the engine silently returns stub responses with `"[NO LLM] Dialog manager running without LLM client"`. No error is logged or raised. A production deploy would show "working" dashboards with no actual AI responses.

- **[MINOR] VAD silence timeout doesn't trigger AI action** — The speech service sends `silence_timeout` event but the engine has no handler for it. Client could wait indefinitely in silence.

---

### 5. Testing — 7/10

**Good:**
- 82 tests across 4 test suites, all passing
- Anti-hallucination regression tests with real scenarios
- Mock dialog tests cover booking flow edge cases
- `pytest-asyncio` used for async test support

**Issues:**

- **[MINOR] No WebSocket tests** — Speech service (ASR, VAD, TTS) and gateway audio relay have zero WebSocket tests. The most latency-sensitive and error-prone part of the system is untested.
- **[MINOR] Test coverage metrics unclear** — No `pytest-cov` configured in any `pyproject.toml`. Coverage numbers from QA report are estimates.
- **[MINOR] YClients adapter has no real integration tests** — The stub returns `False` for `is_available()`, so nothing tests actual YClients API interaction.

---

### 6. Performance — 5/10

**Good:**
- Async I/O throughout (FastAPI + asyncpg + httpx async)
- SQLAlchemy connection pooling configured (pool_size=5, max_overflow=10)
- Redis has TTL on all keys (SESSION_TTL=7200s)
- `ltrim` on Redis message history prevents unbounded memory growth

**Issues:**

- **[MAJOR] `_get_tenant()` called on every API request** — Every booking endpoint calls `_get_tenant()` which does a separate SELECT query. In a multi-call dialog (services → masters → slots → create_booking), this means 4+ identical tenant lookups. No Redis caching for tenant data.

- **[MAJOR] No client-side caching for service/master catalogs** — Service and master lists are fetched from DB on every dialog turn. These are read-heavy, rarely-change datasets that should be cached in Redis with a 5-minute TTL.

- **[MAJOR] Gateway WebSocket architecture creates 4 concurrent connections per call** — Each active call opens 4 WebSocket streams (ASR, VAD, engine audio, TTS) + the SIP connection. At 50 concurrent calls, that's 200+ active WebSocket connections. The architecture mentions pjsua2 processing limits but doesn't address WebSocket scaling.

- **[BUG] `BookingServiceClient` creates a new httpx.AsyncClient per instance** — `ToolExecutor.__init__` creates a `BookingServiceClient` which creates its own `AsyncClient`. If multiple `ToolExecutor` instances exist, they won't share a connection pool.

- **[MINOR] No connection pooling for Redis** — `redis.from_url()` creates a single connection. Under load, `redis-py` will queue requests. Consider connection pool for production.

---

### 7. API Design — 7/10

**Good:**
- RESTful resource naming (`/tenants/{id}/bookings`, `/tenants/{id}/masters`)
- Proper HTTP methods (GET for reads, POST for creates, PATCH for updates, DELETE for cancellations)
- Consistent error format (`{"error": "CODE", "message": "..."}`)
- Proper status codes (201 for create, 404 for not found, 409 for conflicts, 422 for validation)
- Pydantic request/response models with regex validation on phone numbers

**Issues:**

- **[BUG] `PATCH /bookings/{id}` overloads multiple actions** — The `action` field in `BookingUpdateRequest` can be `reschedule | update_service | update_master | cancel`. Cancelling via PATCH is semantically incorrect — DELETE is the proper method for cancellation. The dedicated `DELETE /bookings/{id}` endpoint already handles cancellations correctly.

- **[MINOR] Mixed UUID/string types across API** — `BookingResponse.booking_id` is `UUID` type, but tool function `update_booking` receives `booking_id` as `str` parameter. The `Master.id` in responses is `str` while `master_id` in requests expects `UUID`. Small inconsistencies that can cause 422 errors.

- **[MINOR] `find_slots` uses `days` query param with default 1, max 14** — Good upper bound. But `date` is optional with server-side default of "today". This makes caching slot results unpredictable.

---

## Critical Issues (Blocking)

### C1. Engine WebSocket endpoint missing — voice pipeline broken
- **File:** `engine/src/main.py`
- **What:** ARCHITECTURE.md §3.3 defines `ws://engine:8002/ws/dialog/{call_id}`, gateway tries to connect to it, but engine has no WS endpoint
- **Impact:** Gateway's `audio_relay` → `_engine_to_client()` will fail immediately. All calls forwarded to owner. AI secretary is non-functional as a voice system.
- **Fix:** Implement WebSocket endpoint in `engine/src/main.py` (or add a simple WS bridge that feeds into the REST `/api/engine/message` endpoint), OR update ARCHITECTURE.md to match REST-only implementation and update gateway to use REST polling.

### C2. LLM client never initialized
- **File:** `engine/src/main.py` line 28
- **What:** `llm_client=None` — the `OpenClawLLMClient` from `engine/src/llm/__init__.py` is defined but never instantiated or wired into the dialog manager
- **Impact:** `process_user_message()` always takes the `else: "[NO LLM]"` branch. No actual AI conversation happens.
- **Fix:** Instantiate `OpenClawLLMClient` in the `lifespan` startup and pass it to `DialogManager`:
  ```python
  from src.llm import OpenClawLLMClient
  llm_client = OpenClawLLMClient(
      base_url=os.getenv("OPENCLAW_API_URL", "http://openclaw:4000"),
      api_key=os.getenv("OPENCLAW_API_KEY", ""),
  )
  dialog_manager = DialogManager(state_manager=state_manager, tool_executor=tool_executor, llm_client=llm_client)
  ```

### C3. Missing `and_` import in routes.py
- **File:** `booking/src/api/routes.py` line 10 (imports) and line ~293 (usage)
- **What:** `and_()` used in SQLAlchemy query but not imported. `from sqlalchemy import select, func, delete` — needs `and_`.
- **Impact:** Runtime `NameError` on `GET /tenants/{id}/clients/by-phone/{phone}`. Blocks the client lookup feature entirely.
- **Fix:** Add `and_` to the import line.

---

## Major Issues (Should Fix Before MVP)

### M1. Docker Compose YAML anchor merge bug
- **File:** `docker-compose.yml` (all services using `<<: [*default-restart, *default-logging]`)
- **What:** Using a list in YAML merge key causes `driver` and `options` from `x-logging` to become top-level service properties instead of nesting under `logging:`
- **Effect:** `docker compose config` fails. The `driver` and `options` keys leak into service root.
- **Fix:** Split into two merge keys:
  ```yaml
  <<: *default-restart
  logging: *default-logging
  ```

### M2. Missing ForeignKey constraints on all ORM models
- **Files:** `booking/src/models/booking.py`, `call.py`, `client.py`, `master.py`, `service.py`, etc.
- **What:** None of the ORM models define `ForeignKey` constraints. Only SQLAlchemy relationships exist (which don't enforce referential integrity at DB level).
- **Effect:** Orphaned records possible. Cascade deletes from architecture SQL schema not enforced.
- **Fix:** Add `ForeignKey` to `mapped_column` definitions:
  ```python
  from sqlalchemy import ForeignKey
  tenant_id: Mapped[uuid.UUID] = mapped_column(
      UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
  )
  ```

### M3. Engine lacks TenantMiddleware
- **File:** `engine/src/main.py`
- **What:** Booking service has `TenantMiddleware` from `shared/middleware/` but engine doesn't import or use it. Engine receives `tenant_id` in request bodies but doesn't validate tenant existence or status.
- **Effect:** Malformed requests could bypass tenant isolation checks.
- **Fix:** Import and wire `TenantMiddleware` in engine's FastAPI app, or add inline validation in `process_user_message()`.

### M4. Celery tasks are stubs — no actual notification sending
- **File:** `notifications/src/tasks.py`
- **What:** The architecture defines reminder sending, audio cleanup, and YClients sync as Celery tasks. But `tasks.py` doesn't contain real implementations — just function signatures with `...`.
- **Effect:** SMS reminders, audio cleanup, and YClients background sync won't work.
- **Fix:** Implement task bodies (query `scheduled_notifications`, send SMS via `sms_provider`, clean S3 audio, sync bookings to YClients).

---

## Minor Issues (Nice to Fix)

### m1. Energy-based VAD instead of Silero VAD
- **File:** `speech/src/main.py`
- **What:** Architecture specifies Silero VAD. Implementation uses RMS threshold (`VAD_RMS_THRESHOLD = 300.0`). Silero is significantly more accurate for telephone audio.
- **Fix:** Add Silero VAD as optional enhancement. The current RMS approach can be kept as fallback.

### m2. `hallucination_log.get_stats()` returns empty dict
- **File:** `engine/src/dialog/guard.py`, `HallucinationLog.get_stats()`
- **What:** `"by_tool": {}` is never populated despite `log()` receiving tool names.
- **Fix:** Track tool-level stats.

### m3. `db.flush()` called in `_get_or_create_client` and again in create_booking
- **File:** `booking/src/api/routes.py`
- **What:** Redundant flushes. Minor performance cost.
- **Fix:** Remove one of the redundant `flush()` calls.

### m4. No WebSocket tests for speech/gateway
- **Files:** `speech/tests/`, `gateway/tests/`
- **What:** No test directories exist for speech service or gateway. The most latency-sensitive parts of the system have zero tests.
- **Fix:** Add pytest with `httpx` WebSocket test client for ASR, VAD, TTS endpoints.

### m5. `sip_password` not encrypted in ORM
- **File:** `booking/src/models/sip.py` (if the field exists)
- **What:** Architecture specifies Fernet encryption for SIP credentials. ORM may not have the field or stores it in plaintext.
- **Fix:** Use `FieldEncryption` for `sip_password` column.

---

## What's Good

### Excellent Architecture Decisions
- **Five-layer isolation** with clear REST/WebSocket contracts between layers
- **Interface-first tool design** using Python `Protocol` classes — makes testing trivial
- **Prompt composability** — base prompt + configurable blocks per tenant is a well-designed system
- **Multi-tenant by design** — `tenant_id` on every table, Redis key prefixes, DID-based routing
- **S3 + B-tree exclusion index** for slot conflict prevention

### Strong Implementation Quality
- **82 passing tests** across shared tools, booking, engine, and notifications
- **Full TypeScript + Next.js 14 admin panel** with server components and proper mobile-responsive design
- **Anti-hallucination guards** with param validation, price range checking, and response cleaning
- **Graceful degradation patterns** — retry with backoff, circuit breaker stubs, structured error codes
- **Telegram bot** with proper anti-spam (30s cooldown), inline keyboards, Markdown formatting
- **Redis dialog state management** with TTL, message trimming, tenant-based key isolation

### Design Quality
- **Design spec** is production-grade: contrast ratios, color philosophy, responsive breakpoints, WCAG accessibility
- **Empty states** for every page (not an afterthought)
- **Error states** with retry buttons
- **Skeleton loading** instead of spinners

### Security-Conscious
- No hardcoded secrets in code
- `.env.example` documents all required variables
- Fernet encryption utility exists for sensitive fields
- HMAC signature verification for Sipuni webhooks

---

## Summary

```
STATUS: CHANGES_REQUESTED
TEST_RESULTS: 82/82 passed
CRITICAL: 3 issues (C1, C2, C3)
MAJOR: 4 issues (M1-M4)
MINOR: 5 issues (m1-m5)
```

The Алло project has an **excellent foundation** — well-architected, well-tested, with clean separation of concerns and strong design. However, the critical issues prevent the core voice pipeline from functioning:

1. The engine has **no WebSocket endpoint** despite the architecture and gateway expecting one (`/ws/dialog/{call_id}`)
2. The **LLM client is never initialized** (`llm_client=None`) — no AI conversation happens
3. A **missing import** (`and_`) will crash the client lookup endpoint at runtime

All three are straightforward to fix (combined effort < 2 hours). Once resolved, the architecture is sound and the codebase is MVP-ready.
