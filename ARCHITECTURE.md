# ARCHITECTURE.md — Алло: Voice AI Secretary

> **Версия:** 1.0 (MVP)
> **Последнее обновление:** 2026-04-29
> **Статус:** Утверждена

---

## Table of Contents

1. [Общая архитектурная схема](#1-общая-архитектурная-схема)
2. [Схема базы данных](#2-схема-базы-данных)
3. [API контракты между слоями](#3-api-контракты-между-слоями)
4. [Схема промптов и tools](#4-схема-промптов-и-tools)
5. [Realtime voice pipeline](#5-realtime-voice-pipeline)
6. [Multi-tenant изоляция](#6-multi-tenant-изоляция)
7. [Обработка ошибок и graceful degradation](#7-обработка-ошибок-и-graceful-degradation)
8. [Безопасность](#8-безопасность)
9. [Инфраструктурная схема](#9-инфраструктурная-схема)
10. [OpenClaw интеграция](#10-openclaw-интеграция)

---

## 1. Общая архитектурная схема

### 1.1 Пятислойная архитектура

Система «Алло» построена как **пять независимых слоёв**, каждый из которых масштабируется и деплоится независимо. Связь между слоями — через REST/WebSocket с явными контрактами (Pydantic v2).

```mermaid
graph TB
    subgraph "Layer 1: Voice Gateway"
        VG[Voice Gateway<br/>FastAPI + pjsua2]
        SIP[Sipuni SIP]
    end

    subgraph "Layer 2: Speech Layer"
        ASR[ASR Service<br/>Yandex SpeechKit]
        TTS[TTS Service<br/>Yandex SpeechKit]
        VAD[VAD Module<br/>Silero VAD]
    end

    subgraph "Layer 3: Conversational Engine"
        CE[Conversational Engine<br/>FastAPI + asyncio]
        LLM[DeepSeek-v4-flash<br/>via OpenClaw REST]
        SS[Session State<br/>Redis]
        PG[Prompt Generator]
    end

    subgraph "Layer 4: Booking & CRM"
        BK[Booking Service<br/>FastAPI]
        DB[(PostgreSQL 15)]
        YC[YClients Adapter]
    end

    subgraph "Layer 5: Admin & Notifications"
        AD[Admin Panel<br/>FastAPI + Jinja2 + HTMX]
        TG[Telegram Bot<br/>via OpenClaw]
        SMS[SMS Service<br/>Sipuni SMS]
    end

    subgraph "OpenClaw"
        OC[OpenClaw Gateway]
        TSP[TS Plugins<br/>= tool wrappers]
        TGB[Telegram Bot Plugin]
    end

    %% Voice Pipeline
    SIP -->|RTP audio| VG
    VG -->|opus/raw PCM| ASR
    VG -->|opus/raw PCM| VAD
    ASR -->|text transcript| CE
    CE -->|text response| TTS
    TTS -->|opus audio| VG
    VAD -->|voice activity events| CE
    VG -->|call events| CE

    %% Engine → Tools
    CE -->|tool calls via REST| TSP
    TSP -.->|REST HTTP| BK
    TSP -.->|REST HTTP| OC

    %% Booking → DB
    BK --> DB
    BK --> YC

    %% Admin
    AD --> DB
    AD --> BK

    %% Notifications
    TG -.->|via OpenClaw| OC
    SMS -->|Sipuni SMS API| SIP

    %% Redis
    CE --> SS
```

### 1.2 Связка с OpenClaw

```mermaid
graph LR
    subgraph "Python World (services)"
        CE[Conversational Engine]
        BK[Booking Service]
        PT[Python Tools Library<br/>shared/tools/]
    end

    subgraph "OpenClaw World (TypeScript)"
        OC[OpenClaw Gateway]
        TGB[TG Bot Plugin]
        BP[Booking Plugin<br/>TS wrapper]
        CP[Calendar Plugin<br/>TS wrapper]
        MP[Masters Plugin<br/>TS wrapper]
    end

    subgraph "External"
        LLM[DeepSeek API]
    end

    CE -->|"HTTP POST /api/v1/tools/booking/*"| BP
    CE -->|"HTTP POST /api/v1/tools/calendar/*"| CP
    CE -->|"HTTP POST /api/v1/tools/masters/*"| MP
    BP -->|"calls"| PT
    PT --> BK
    CE -->|"LLM inference"| OC
    OC --> LLM
    TG -.->|"via"| OC
```

**Ключевое решение:** OpenClaw используется **только для текстовых каналов** (Telegram-бот) и как **прокси для LLM** (DeepSeek). Голосовой движок — полностью отдельный Python-сервис.
Tools реализованы как **Python-библиотека** в `shared/tools/`, а OpenClaw-плагины — **TypeScript-обёртки**, которые проксируют REST-вызовы к Python.

### 1.3 Модульная структура проекта

```
allo/
├── gateway/                 # Layer 1: Voice Gateway (SIP)
│   ├── src/
│   │   ├── sip/             # pjsua2 integration
│   │   ├── audio/           # Audio stream processing
│   │   ├── pipeline/        # Voice pipeline orchestrator
│   │   └── api/             # REST API for call control
│   ├── Dockerfile
│   └── pyproject.toml
│
├── speech/                  # Layer 2: Speech Services
│   ├── src/
│   │   ├── asr/             # Yandex SpeechKit ASR
│   │   ├── tts/             # Yandex SpeechKit TTS
│   │   └── vad/             # Silero VAD
│   ├── Dockerfile
│   └── pyproject.toml
│
├── engine/                  # Layer 3: Conversational Engine
│   ├── src/
│   │   ├── dialog/          # Dialog manager
│   │   ├── prompts/         # Prompt templates
│   │   ├── tools/           # Tool call integration
│   │   └── state/           # Redis session state
│   ├── tests/
│   │   ├── mock_dialogs/    # 100+ test dialogs
│   │   └── anti_hallucination/
│   ├── Dockerfile
│   └── pyproject.toml
│
├── booking/                 # Layer 4: Booking & CRM
│   ├── src/
│   │   ├── api/             # REST API
│   │   ├── calendar/        # Internal calendar logic
│   │   ├── yclients/        # YClients adapter
│   │   └── models/          # SQLAlchemy models
│   ├── migrations/          # Alembic
│   ├── Dockerfile
│   └── pyproject.toml
│
├── admin/                   # Layer 5: Admin Panel
│   ├── src/
│   │   ├── web/             # Jinja2 / HTMX pages
│   │   ├── api/             # Admin REST API
│   │   └── wizard/          # Onboarding wizard
│   ├── Dockerfile
│   └── pyproject.toml
│
├── notifications/           # Layer 5: Notifications
│   ├── src/
│   │   ├── telegram/        # TG bot logic
│   │   ├── sms/             # Sipuni SMS
│   │   └── templates/       # Message templates
│   ├── Dockerfile
│   └── pyproject.toml
│
├── shared/                  # Shared code
│   ├── tools/               # Python tools library
│   │   ├── protocols.py     # Tool interfaces (Protocol classes)
│   │   ├── registry.py      # Tool registry
│   │   ├── booking.py       # Booking tools
│   │   ├── masters.py       # Masters tools
│   │   ├── services.py      # Services tools
│   │   ├── calendar.py      # Calendar/slots tools
│   │   └── escalation.py    # Escalation tools
│   ├── models/              # Shared Pydantic models
│   ├── exceptions/          # Shared error classes
│   └── utils/               # Utilities (logging, retry, etc.)
│
├── openclaw-plugins/        # OpenClaw TS plugins
│   ├── booking-plugin/
│   ├── calendar-plugin/
│   ├── masters-plugin/
│   └── telegram-bot/
│
├── docker-compose.yml
├── docker-compose.override.yml  # Dev overrides
├── Makefile
└── .github/
    └── workflows/
        ├── test.yml
        └── deploy.yml
```

---

## 2. Схема базы данных

### 2.1 Полная ER-диаграмма

```mermaid
erDiagram
    tenants ||--o{ services : "has"
    tenants ||--o{ masters : "has"
    tenants ||--o{ clients : "has"
    tenants ||--o{ bookings : "has"
    tenants ||--o{ calls : "has"
    tenants ||--o{ prompt_profiles : "has"
    tenants ||--o{ notification_settings : "has"
    tenants ||--o{ sip_settings : "has"

    masters ||--o{ master_services : "works"
    services ||--o{ master_services : "offers"

    clients ||--o{ bookings : "makes"
    masters ||--o{ bookings : "assigned_to"

    bookings ||--o{ booking_history : "logs"
    bookings ||--o{ call_bookings : "linked"

    calls ||--o{ call_transcripts : "has"
    calls ||--o{ call_bookings : "creates"

    prompt_profiles ||--o{ prompt_blocks : "configures"

    notification_settings ||--o{ scheduled_notifications : "generates"
```

### 2.2 Описание таблиц

#### tenants
Таблица-владелец. Все данные изолированы через `tenant_id`.

```sql
CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,          -- "Салон красоты Элегант"
    slug            VARCHAR(100) UNIQUE NOT NULL,    -- "elegant"
    phone           VARCHAR(20) NOT NULL,            -- Номер для переадресации
    timezone        VARCHAR(50) NOT NULL DEFAULT 'Europe/Moscow',
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active','suspended','deleted')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
```

#### services
Услуги салона (загружаются из YClients или создаются вручную).

```sql
CREATE TABLE services (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    yclients_id     INTEGER,                         -- ID в YClients (nullable)
    name            VARCHAR(255) NOT NULL,            -- "Стрижка женская"
    description     TEXT,
    duration_min    INTEGER NOT NULL,                 -- 60 (минут)
    price_rub       NUMERIC(10,2) NOT NULL,
    category        VARCHAR(100),                     -- "стрижки", "окрашивание"
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_tenant_yclients UNIQUE (tenant_id, yclients_id)
);

CREATE INDEX idx_services_tenant ON services(tenant_id);
CREATE INDEX idx_services_category ON services(tenant_id, category);
```

#### masters
Мастера (сотрудники) салона.

```sql
CREATE TABLE masters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    yclients_id     INTEGER,
    name            VARCHAR(255) NOT NULL,            -- "Анна Петрова"
    phone           VARCHAR(20),
    specialization  VARCHAR(255),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_masters_tenant ON masters(tenant_id);
```

#### master_services
M2M связь мастеров и услуг (какие услуги делает мастер).

```sql
CREATE TABLE master_services (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    master_id       UUID NOT NULL REFERENCES masters(id) ON DELETE CASCADE,
    service_id      UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,

    CONSTRAINT unique_master_service UNIQUE (master_id, service_id)
);

CREATE INDEX idx_master_services_master ON master_services(master_id);
CREATE INDEX idx_master_services_service ON master_services(service_id);
```

#### clients
Клиенты — идентифицируются по номеру телефона.

```sql
CREATE TABLE clients (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    phone           VARCHAR(20) NOT NULL,
    name            VARCHAR(255),                     -- "Мария Ивановна"
    total_visits    INTEGER NOT NULL DEFAULT 0,
    last_visit_at   TIMESTAMPTZ,
    preferences     JSONB DEFAULT '{}',               -- предпочтения (мастер, услуги)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_tenant_phone UNIQUE (tenant_id, phone)
);

CREATE INDEX idx_clients_tenant ON clients(tenant_id);
CREATE INDEX idx_clients_phone ON clients(tenant_id, phone);
```

#### bookings
Записи на услуги. Центральная таблица бизнес-логики.

```sql
CREATE TABLE bookings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    client_id       UUID NOT NULL REFERENCES clients(id),
    master_id       UUID NOT NULL REFERENCES masters(id),
    service_id      UUID NOT NULL REFERENCES services(id),
    yclients_id     INTEGER,                         -- ID записи в YClients
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','confirmed','completed',
                                      'cancelled','no_show')),
    start_at        TIMESTAMPTZ NOT NULL,
    end_at          TIMESTAMPTZ NOT NULL,
    price_rub       NUMERIC(10,2) NOT NULL,
    comment         TEXT,                             -- комментарий клиента
    source          VARCHAR(20) NOT NULL DEFAULT 'phone'
                    CHECK (source IN ('phone','telegram','admin')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bookings_tenant ON bookings(tenant_id);
CREATE INDEX idx_bookings_client ON bookings(tenant_id, client_id);
CREATE INDEX idx_bookings_master ON bookings(tenant_id, master_id);
CREATE INDEX idx_bookings_start ON bookings(tenant_id, start_at);
CREATE INDEX idx_bookings_status ON bookings(tenant_id, status);
CREATE INDEX idx_bookings_date ON bookings(tenant_id, start_at::date);

-- Исключаем бронирования с пересекающимися временными слотами
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE INDEX idx_bookings_no_overlap
    ON bookings USING GIST (tenant_id, master_id,
                            tstzrange(start_at, end_at) WITH =)
    WHERE status NOT IN ('cancelled', 'no_show');
```

#### booking_history
Аудит изменений статуса записи.

```sql
CREATE TABLE booking_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id      UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    from_status     VARCHAR(20),
    to_status       VARCHAR(20) NOT NULL,
    changed_by      VARCHAR(50) NOT NULL,             -- 'ai', 'admin', 'yclients'
    reason          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_book_hist_booking ON booking_history(booking_id);
```

#### calls
Звонки. Аудио хранится 90 дней в S3, расшифровки — бессрочно.

```sql
CREATE TABLE calls (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    caller_phone    VARCHAR(20) NOT NULL,
    client_id       UUID REFERENCES clients(id),     -- nullable (новый клиент)
    did             VARCHAR(20) NOT NULL,             -- набранный номер (DID)
    session_id      VARCHAR(255),                     -- Sipuni session ID
    status          VARCHAR(30) NOT NULL DEFAULT 'in_progress'
                    CHECK (status IN ('in_progress','completed','failed',
                                      'escalated','missed')),
    duration_sec    INTEGER,                          -- длительность звонка
    audio_key       VARCHAR(500),                     -- путь в S3 (срок 90 дней)
    transcript_s3   VARCHAR(500),                     -- расшифровка в S3 (бессрочно)
    transcript_text TEXT,                             -- расшифровка (дублируется в БД)
    result          VARCHAR(50),                      -- 'booking_created','info_only','escalated','cancelled'
    error_reason    TEXT,                             -- если звонок с ошибкой
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ
);

CREATE INDEX idx_calls_tenant ON calls(tenant_id);
CREATE INDEX idx_calls_caller ON calls(tenant_id, caller_phone);
CREATE INDEX idx_calls_created ON calls(tenant_id, created_at DESC);
CREATE INDEX idx_calls_status ON calls(tenant_id, status);

-- Аудио удаляется через 90 дней (cleanup job)
CREATE INDEX idx_calls_cleanup ON calls(tenant_id, created_at)
    WHERE audio_key IS NOT NULL;
```

#### call_transcripts
Детальная расшифровка: каждая фраза AI и клиента.

```sql
CREATE TABLE call_transcripts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id         UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    speaker         VARCHAR(10) NOT NULL CHECK (speaker IN ('ai','client')),
    text            TEXT NOT NULL,
    start_sec       NUMERIC(8,3),                    -- секунда от начала звонка
    end_sec         NUMERIC(8,3),
    tool_calls      JSONB,                            -- какие tools вызывались
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_transcripts_call ON call_transcripts(call_id);
```

#### call_bookings
M2M связь звонков и созданных записей.

```sql
CREATE TABLE call_bookings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id         UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    booking_id      UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,

    CONSTRAINT unique_call_booking UNIQUE (call_id, booking_id)
);

CREATE INDEX idx_call_bookings_call ON call_bookings(call_id);
CREATE INDEX idx_call_bookings_booking ON call_bookings(booking_id);
```

#### prompt_profiles
Профили промптов. На тенанта может быть один активный профиль.

```sql
CREATE TABLE prompt_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,            -- "beauty_salon"
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_active_profile UNIQUE (tenant_id)
        WHERE is_active = TRUE
);

CREATE INDEX idx_prompt_profiles_tenant ON prompt_profiles(tenant_id);
```

#### prompt_blocks
Конфигурируемые блоки промпта (название, тон, приветствие, правила).

```sql
CREATE TABLE prompt_blocks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id      UUID NOT NULL REFERENCES prompt_profiles(id) ON DELETE CASCADE,
    block_key       VARCHAR(100) NOT NULL,            -- 'greeting', 'tone', 'rules', 'farewell'
    content         TEXT NOT NULL,                    -- текст блока (Markdown)
    position        INTEGER NOT NULL DEFAULT 0,       -- порядок сборки
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_block_key UNIQUE (profile_id, block_key)
);

CREATE INDEX idx_prompt_blocks_profile ON prompt_blocks(profile_id);
```

#### sip_settings
SIP-настройки тенанта (индивидуальный DID).

```sql
CREATE TABLE sip_settings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    did             VARCHAR(20) UNIQUE NOT NULL,      -- номер телефона
    forward_number  VARCHAR(20),                      -- номер для переадресации
    sip_user        VARCHAR(100),                     -- SIP username на Sipuni
    sip_password    VARCHAR(255) ENCRYPTED,           -- зашифрованный пароль
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sip_tenant ON sip_settings(tenant_id);
CREATE INDEX idx_sip_did ON sip_settings(did);
```

#### notification_settings
Настройки уведомлений тенанта.

```sql
CREATE TABLE notification_settings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    telegram_chat_id    VARCHAR(100),                 -- Telegram chat ID владельца
    sms_enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    reminder_day    BOOLEAN NOT NULL DEFAULT TRUE,    -- напоминание за день
    reminder_hour   BOOLEAN NOT NULL DEFAULT TRUE,    -- напоминание за час
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_tenant_notif UNIQUE (tenant_id)
);
```

#### scheduled_notifications
Очередь запланированных уведомлений (создаются Celery beat).

```sql
CREATE TABLE scheduled_notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id      UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    notification_type VARCHAR(20) NOT NULL
                    CHECK (type IN ('sms_day','sms_hour','telegram')),
    send_at         TIMESTAMPTZ NOT NULL,
    sent            BOOLEAN NOT NULL DEFAULT FALSE,
    sent_at         TIMESTAMPTZ,
    error           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sched_notif_send ON scheduled_notifications(send_at, sent)
    WHERE sent = FALSE;
```

### 2.3 Raw SQL миграции vs Alembic

**Выбор:** Alembic + автогенерация из SQLAlchemy 2 моделей.

```
booking/migrations/
├── versions/
│   ├── 0001_initial.py          # Все таблицы из секции 2.2
│   ├── 0002_add_call_bookings.py
│   └── ...
├── env.py
├── alembic.ini
└── script.py.mako
```

**Seed data (`seed.py`):**
- Тестовый тенант "Салон красоты Элегант" (slug: `elegant`)
- 5 услуг, 3 мастера, prompt_profile `beauty_salon` с 4 блоками
- Тестовый тарифный план

### 2.4 Миграции данных (data migrations)

Отдельные скрипты в `booking/migrations/data/`:
- `sync_yclients_services.py` — импорт услуг из YClients
- `cleanup_old_audio.py` — удаление аудио старше 90 дней

---

## 3. API контракты между слоями

### 3.1 Voice Gateway → Speech (ASR)

**Протокол:** WebSocket, бинарные фреймы (аудио) ↔ JSON (расшифровки)

#### ASR Request Stream (Gateway → ASR Service)

```
WS ws://speech:8001/ws/asr/{call_id}

Frame 1 (JSON text):
{
  "event": "start",
  "call_id": "uuid",
  "tenant_id": "uuid",
  "sample_rate": 8000,          // 8 кГц для телефонии
  "format": "opus",             // opus | raw_pcm_s16le
  "language": "ru-RU",
  "custom_vocabulary": ["стрижка", "окрашивание", "маникюр", "педикюр", "биозавивка"]
}

Frame 2..N (binary audio chunks):
[opus audio frame]

Frame N (JSON text, final):
{
  "event": "end"
}
```

#### ASR Response Stream (ASR Service → Gateway)

```
Frame 1 (JSON text, intermediate):
{
  "event": "transcript",
  "call_id": "uuid",
  "text": "здравствуйте я хотела бы",
  "is_final": false,
  "confidence": 0.89
}

Frame 2 (JSON text, final):
{
  "event": "transcript",
  "call_id": "uuid",
  "text": "здравствуйте я хотела бы записаться на стрижку",
  "is_final": true,
  "confidence": 0.95,
  "words": [
    {"text": "здравствуйте", "start_sec": 0.3, "end_sec": 1.1, "confidence": 0.98},
    {"text": "стрижку", "start_sec": 4.2, "end_sec": 4.8, "confidence": 0.91}
  ]
}

Frame 3 (JSON text, error):
{
  "event": "error",
  "call_id": "uuid",
  "code": "ASR_TIMEOUT",
  "message": "No speech detected for 30 seconds"
}
```

### 3.2 Voice Gateway → VAD Service

**Протокол:** WebSocket, бинарные фреймы (аудио) ↔ JSON (события)

#### VAD Stream

```
WS ws://speech:8001/ws/vad/{call_id}

Frame 1 (JSON start):
{
  "event": "start",
  "call_id": "uuid",
  "sample_rate": 8000,
  "format": "opus",
  "vad_level": 2              // Silero VAD sensitivity (0-3)
}

Frame 2..N (binary audio):
[opus audio frame]

Response frames:
{
  "event": "speech_start",
  "call_id": "uuid",
  "time_sec": 12.5
}
{
  "event": "speech_end",
  "call_id": "uuid",
  "time_sec": 17.3,
  "duration_sec": 4.8
}
{
  "event": "silence_timeout",
  "call_id": "uuid",
  "time_sec": 35.0
}
```

### 3.3 Speech (ASR) → Engine

**Протокол:** WebSocket (через Gateway) + REST

```
WS ws://engine:8002/ws/dialog/{call_id}

From Gateway (client transcript):
{
  "event": "client_speech",
  "call_id": "uuid",
  "tenant_id": "uuid",
  "text": "хочу записаться на маникюр на завтра",
  "is_final": true,
  "words": [...]
}

From Engine (AI response):
{
  "event": "ai_response",
  "call_id": "uuid",
  "text": "На завтра, 30 апреля, у нас есть свободное время в 14:00 и 16:00. Вам какое удобнее?",
  "tts_priority": true,       // параллельная выдача TTS
  "tool_calls": [
    {
      "tool": "find_slots",
      "args": {
        "service": "маникюр",
        "date": "2026-04-30",
        "master_name": null
      },
      "result": {
        "slots": [
          {"master": "Анна", "start": "2026-04-30T14:00:00", "end": "2026-04-30T15:00:00"},
          {"master": "Елена", "start": "2026-04-30T16:00:00", "end": "2026-04-30T17:00:00"}
        ]
      }
    }
  ]
}

From Engine (action result):
{
  "event": "action",
  "call_id": "uuid",
  "action": "create_booking",
  "result": {
    "booking_id": "uuid",
    "status": "confirmed",
    "summary": "Маникюр у Анны, 30 апреля в 14:00, 1500 ₽"
  }
}
```

### 3.4 Engine → Booking Service (через OpenClaw TS Plugin → REST)

**Протокол:** REST HTTP

```yaml
# GET services
GET /api/v1/tenants/{tenant_id}/services
Query: ?category=стрижки&is_active=true
Response 200:
{
  "services": [
    {
      "id": "uuid",
      "name": "Стрижка женская",
      "duration_min": 60,
      "price_rub": 2500.00,
      "category": "стрижки"
    }
  ]
}

# GET masters
GET /api/v1/tenants/{tenant_id}/masters
Query: ?service_id=uuid&is_active=true
Response 200:
{
  "masters": [
    {
      "id": "uuid",
      "name": "Анна Петрова",
      "specialization": "Стрижки, окрашивание"
    }
  ]
}

# GET available slots
GET /api/v1/tenants/{tenant_id}/slots
Query:
  - master_id: uuid
  - service_id: uuid
  - date: 2026-04-30
Response 200:
{
  "slots": [
    {
      "start": "2026-04-30T14:00:00+03:00",
      "end": "2026-04-30T15:00:00+03:00",
      "master_id": "uuid",
      "master_name": "Анна Петрова"
    }
  ]
}

# POST booking
POST /api/v1/tenants/{tenant_id}/bookings
Request:
{
  "client_phone": "+79161234567",
  "client_name": "Мария",
  "master_id": "uuid",
  "service_id": "uuid",
  "start_at": "2026-04-30T14:00:00+03:00",
  "source": "phone"
}
Response 201:
{
  "booking_id": "uuid",
  "status": "confirmed",
  "yclients_id": 98765,
  "summary": "Маникюр у Анны, 30 апреля в 14:00, 1500 ₽"
}
Errors:
  409: {"error": "SLOT_TAKEN", "message": "Время 14:00 уже занято"}
  422: {"error": "SERVICE_UNAVAILABLE", "message": "Услуга временно недоступна"}

# GET booking
GET /api/v1/tenants/{tenant_id}/bookings/{booking_id}
Response 200:
{
  "booking_id": "uuid",
  "status": "confirmed",
  "client": {"id": "uuid", "name": "Мария", "phone": "+79161234567"},
  "master": {"id": "uuid", "name": "Анна Петрова"},
  "service": {"name": "Маникюр", "price_rub": 1500.00},
  "start_at": "2026-04-30T14:00:00+03:00",
  "end_at": "2026-04-30T15:00:00+03:00"
}

# PATCH booking (reschedule)
PATCH /api/v1/tenants/{tenant_id}/bookings/{booking_id}
Request:
{
  "action": "reschedule",       // reschedule | cancel | update_service
  "start_at": "2026-05-01T10:00:00+03:00",
  "master_id": "uuid",
  "reason": "Клиент попросил перенести"
}
Response 200:
{
  "booking_id": "uuid",
  "status": "confirmed",
  "old_start": "2026-04-30T14:00:00+03:00",
  "new_start": "2026-05-01T10:00:00+03:00"
}

# DELETE booking (cancel)
DELETE /api/v1/tenants/{tenant_id}/bookings/{booking_id}
?reason=client_cancel
Response 200:
{
  "booking_id": "uuid",
  "status": "cancelled",
  "cancelled_at": "2026-04-29T21:52:00+03:00"
}

# GET business info
GET /api/v1/tenants/{tenant_id}/info
Response 200:
{
  "tenant_name": "Салон красоты Элегант",
  "address": "ул. Тверская, д. 15",
  "phone": "+74951234567",
  "work_hours": {
    "mon-fri": "09:00-21:00",
    "sat": "10:00-20:00",
    "sun": "10:00-18:00"
  },
  "next_holiday": "2026-05-01",    // дополнительный выходной
  "description": "Салон красоты премиум-класса в центре Москвы"
}

# POST escalate (перевод звонка владельцу)
POST /api/v1/tenants/{tenant_id}/escalate
Request:
{
  "call_id": "uuid",
  "reason": "client_complaint",
  "client_phone": "+79161234567"
}
Response 200:
{
  "forward_to": "+79991234567",     // номер владельца
  "action": "transfer"
}

# GET client by phone
GET /api/v1/tenants/{tenant_id}/clients/by-phone/{phone}
Response 200:
{
  "client": {
    "id": "uuid",
    "name": "Мария Иванова",
    "phone": "+79161234567",
    "total_visits": 5,
    "last_visit_at": "2026-03-15T14:00:00+03:00",
    "preferred_master_id": "uuid",
    "preferred_services": ["стрижка", "окрашивание"]
  },
  "last_booking": {
    "service": "Стрижка женская",
    "master": "Анна Петрова",
    "date": "2026-03-15"
  }
}
Response 404: {"error": "CLIENT_NOT_FOUND", "message": "Клиент не найден"}
```

### 3.5 Engine → OpenClaw (LLM inference)

**Протокол:** REST HTTP

```
POST http://openclaw:4000/api/llm/chat
Headers:
  X-API-Key: ${OPENCLAW_API_KEY}
Request:
{
  "model": "deepseek/deepseek-v4-flash",
  "messages": [
    {"role": "system", "content": "Ты голосовой AI-секретарь салона красоты..."},
    {"role": "user", "content": "здравствуйте хочу записаться на стрижку"}
  ],
  "tools": [...tool_definitions...],
  "temperature": 0.3,
  "max_tokens": 500,
  "stream": true
}
Response (SSE stream):
event: message
data: {"role": "assistant", "content": "Здравствуйте! Подскажите, к какому мастеру вы хотите записаться?"}

event: tool_call
data: {"name": "find_slots", "arguments": {...}}

event: done
data: {"usage": {"prompt_tokens": 450, "completion_tokens": 120}}
```

### 3.6 Engine → TTS Service

**Протокол:** gRPC (бинарный аудиопоток)

```protobuf
service TTSService {
  rpc Synthesize(stream TTSRequest) returns (stream TTSResponse);
}

message TTSRequest {
  string call_id = 1;
  string text = 2;
  string voice = 3;       // "alena" | "ermil"
  int32 sample_rate = 4;  // 8000
  bool streaming_mode = 5; // параллельная выдача
}

message TTSResponse {
  string call_id = 1;
  bytes audio_chunk = 2;    // opus frame
  int32 chunk_sequence = 3;
  bool is_final = 4;
  string text_spoken = 5;
}
```

### 3.7 Admin Panel → Booking Service

**Протокол:** REST HTTP (внутренняя сеть)

```
# All endpoints under /api/admin/v1/

GET    /tenants                          # Список тенантов
POST   /tenants                          # Создать тенанта
GET    /tenants/{id}                     # Информация о тенанте
PATCH  /tenants/{id}                     # Обновить тенанта

GET    /tenants/{id}/stats/calls         # Статистика звонков
GET    /tenants/{id}/stats/bookings      # Статистика записей
GET    /tenants/{id}/stats/escalations   # Статистика эскалаций

GET    /tenants/{id}/calls               # История звонков
GET    /tenants/{id}/calls/{call_id}     # Детали звонка (+ расшифровка)

GET    /tenants/{id}/prompt-profile      # Профиль промпта
PUT    /tenants/{id}/prompt-profile      # Обновить блоки промпта

GET    /tenants/{id}/sip-settings        # SIP-настройки
PUT    /tenants/{id}/sip-settings        # Обновить SIP-настройки

POST   /tenants/{id}/test-call           # Инициировать тестовый звонок
```

---

## 4. Схема промптов и tools

### 4.1 Архитектура промпта

Промпт — это **композиция базового промпта + конфигурируемых блоков**:

```
┌──────────────────────────────────────────────┐
│              System Prompt                     │
├──────────────────────────────────────────────┤
│  [BASE] — фиксированная часть                 │
│  • Роль: голосовой AI-секретарь               │
│  • Правила: любые конфигурации                │
│  • Формат ответов                              │
│  • Запреты (галлюцинации, выдумывание)        │
│  • Инструкции по tool calling                  │
├──────────────────────────────────────────────┤
│  [CONFIGURABLE BLOCKS] — из prompt_profile    │
│  • greeting    — приветствие                   │
│  • tone        — тон (формально/дружелюбно)    │
│  • business_info — название, адрес, часы работы│
│  • services    — список услуг с ценами         │
│  • masters     — список мастеров              │
│  • rules       — особые правила               │
│  • farewell    — прощание                      │
├──────────────────────────────────────────────┤
│  [CONTEXT] — динамическая часть               │
│  • client_info — имя клиента, история          │
│  • dialog_history — последние N сообщений     │
│  • current_call_state — состояние звонка       │
└──────────────────────────────────────────────┘
```

### 4.2 Базовый промпт

```python
# engine/src/prompts/base.py

BASE_SYSTEM_PROMPT = """Ты — голосовой AI-секретарь компании "{business_name}".
Твоя задача — записывать клиентов на услуги через телефонный разговор.

## Фундаментальные правила
1. Ты говоришь ПО-РУССКИ. Всегда. Даже если клиент пытается говорить на другом языке.
2. Ты НИКОГДА не выдумываешь данные. Все имена, цены, время берутся ТОЛЬКО из результатов вызова tools.
3. Если ты не уверена — переспроси. Не додумывай.
4. Ты говоришь коротко, естественно, как живой человек. Используй "ага", "минутку", "сейчас посмотрю".
5. Никаких причастий и деепричастных оборотов. Никаких канцеляризмов. Разговорный русский язык.

## Стиль общения
- Короткие фразы (2-4 слова максимум на вопрос)
- Дружелюбно, но профессионально
- Если нужно уточнить — спроси одним вопросом, не перечисляй варианты
- Подтверждай действие: "Записала вас к Анне на завтра в 14:00"
- Не повторяй информацию, которую клиент уже сказал

## Правило "Просто спросить"
Если клиент явно не хочет записываться (сказал "нет, спасибо", "я просто спросить", "позже", "может быть"):
1. Ответь кратко на его вопрос (если был вопрос)
2. Скажи: "Я записала, если передумаете — перезвоните. Всего доброго!"
3. Скажи "До свидания!"
НИКАКИХ попыток уговорить. Никаких "может всё-таки запишем". Никаких additional offers.

## Правило эскалации
Если клиент выражает недовольство, жалуется, хамит:
1. Скажи: "Извините, сейчас соединю вас с администратором"
2. Запиши причину в escalate tool
3. Вызови escalate_to_human()

## Инструменты
Ты можешь использовать следующие инструменты. Вызывай их, когда нужны данные.
НЕ ВЫДУМЫВАЙ результаты. Если инструмент вернул ошибку — сообщи клиенту что-то пошло не так.

## Длительность звонка
Старайся не затягивать. Типичная запись: 30-60 секунд.
Не рассказывай про акции и доп. услуги, если клиент не спросил.
"""

async def build_system_prompt(
    tenant_id: str,
    prompt_profile: PromptProfile,
    client_info: Optional[ClientInfo] = None,
) -> str:
    """Собирает финальный system prompt из блоков."""
    blocks = prompt_profile.blocks

    # Заменяем плейсхолдеры в BASE
    prompt = BASE_SYSTEM_PROMPT.replace("{business_name}", blocks['business_name'])

    # Добавляем конфигурируемые блоки
    for key in ['greeting', 'tone', 'services', 'masters', 'rules', 'farewell']:
        if key in blocks:
            prompt += f"\n\n## {key.upper()}\n{blocks[key]}"

    # Добавляем контекст клиента
    if client_info:
        prompt += f"""
## КОНТЕКСТ КЛИЕНТА
Имя: {client_info.name}
Всего визитов: {client_info.total_visits}
Последний визит: {client_info.last_visit_at}
Предпочитаемый мастер: {client_info.preferred_master_name or 'не указан'}
Предпочитаемые услуги: {', '.join(client_info.preferred_services) or 'не указаны'}
"""
    return prompt
```

### 4.3 Пример prompt_profile для beauty_salon

```json
{
  "name": "beauty_salon",
  "is_active": true,
  "blocks": [
    {
      "block_key": "greeting",
      "content": "Салон красоты «Элегант», здравствуйте! Чем могу помочь?",
      "position": 1
    },
    {
      "block_key": "tone",
      "content": "Ты общаешься дружелюбно, но без панибратства. Обращайся на «Вы».",
      "position": 2
    },
    {
      "block_key": "rules",
      "content": "Правила салона:\n- Отмена записи — за 2 часа\n- Опоздание более 15 минут — перенос\n- 152-ФЗ: обязательно скажи «В целях контроля качества наш разговор может быть записан» в начале",
      "position": 3
    },
    {
      "block_key": "farewell",
      "content": "Будем ждать вас в салоне! Если что-то изменится — перезвоните. Всего доброго!",
      "position": 4
    }
  ]
}
```

### 4.4 Все 9 tools — сигнатуры

```python
# shared/tools/ — Python Library

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field


# ============= 1. get_services =============

class GetServicesParams(BaseModel):
    category: Optional[str] = Field(
        None, description="Фильтр по категории: стрижки, окрашивание, маникюр, педикюр, уход"
    )

class Service(BaseModel):
    id: str
    name: str = Field(description="Название услуги")
    duration_min: int = Field(description="Длительность в минутах")
    price_rub: float = Field(description="Цена в рублях")
    category: Optional[str] = None
    description: Optional[str] = None

class GetServicesResult(BaseModel):
    services: List[Service]

async def get_services(
    tenant_id: str,
    params: GetServicesParams,
    booking_service: BookingServiceInterface,
) -> GetServicesResult:
    """
    Возвращает список услуг салона.
    Вызывается в начале диалога для показа списка.
    Может фильтроваться по категории.
    """
    ...


# ============= 2. get_masters =============

class GetMastersParams(BaseModel):
    service_id: Optional[str] = Field(
        None, description="ID услуги — показать только мастеров, которые делают эту услугу"
    )

class Master(BaseModel):
    id: str
    name: str = Field(description="Имя мастера")
    specialization: Optional[str] = Field(description="Специализация мастера")
    rating: Optional[float] = None

class GetMastersResult(BaseModel):
    masters: List[Master]

async def get_masters(
    tenant_id: str,
    params: GetMastersParams,
    booking_service: BookingServiceInterface,
) -> GetMastersResult:
    """
    Возвращает список мастеров. Если указан service_id — фильтрует по услуге.
    """
    ...


# ============= 3. find_slots =============

class FindSlotsParams(BaseModel):
    master_id: Optional[str] = Field(
        None, description="ID мастера (если не указан — все мастера)"
    )
    service_id: Optional[str] = Field(
        None, description="ID услуги (для расчёта длительности)"
    )
    date: date = Field(description="Дата в формате YYYY-MM-DD")

class TimeSlot(BaseModel):
    start: datetime = Field(description="Начало слота (ISO 8601)")
    end: datetime = Field(description="Конец слота (ISO 8601)")
    master_id: str
    master_name: str

class FindSlotsResult(BaseModel):
    slots: List[TimeSlot]

async def find_slots(
    tenant_id: str,
    params: FindSlotsParams,
    booking_service: BookingServiceInterface,
) -> FindSlotsResult:
    """
    Ищет свободные временные слоты на указанную дату.
    Проверяет: внутренний календарь + YClients (если доступен).
    Возвращает пустой список, если слотов нет.
    """
    ...


# ============= 4. create_booking =============

class CreateBookingParams(BaseModel):
    client_phone: str = Field(description="Номер телефона клиента в формате +7...")
    client_name: str = Field(description="Имя клиента")
    master_id: str = Field(description="ID мастера")
    service_id: str = Field(description="ID услуги")
    start_at: datetime = Field(description="Дата и время начала в ISO 8601")
    comment: Optional[str] = Field(None, description="Комментарий клиента")

class CreateBookingResult(BaseModel):
    booking_id: str
    status: str = Field(description="confirmed | pending (если в YClients ошибка)")
    yclients_id: Optional[int] = None
    summary: str = Field(description="Человекочитаемое описание записи")

async def create_booking(
    tenant_id: str,
    params: CreateBookingParams,
    booking_service: BookingServiceInterface,
) -> CreateBookingResult:
    """
    Создаёт запись. Сначала во внутреннем календаре, потом в YClients (если доступен).
    Если YClients недоступен — запись создаётся только во внутреннем календаре.
    """
    ...


# ============= 5. find_booking =============

class FindBookingParams(BaseModel):
    client_phone: str = Field(description="Номер телефона клиента")
    status: Optional[str] = Field(None, description="Фильтр по статусу")
    limit: int = Field(5, description="Максимум записей")

class BookingInfo(BaseModel):
    booking_id: str
    service_name: str
    master_name: str
    start_at: datetime
    status: str
    price_rub: float

class FindBookingResult(BaseModel):
    bookings: List[BookingInfo]

async def find_booking(
    tenant_id: str,
    params: FindBookingParams,
    booking_service: BookingServiceInterface,
) -> FindBookingResult:
    """
    Ищет существующие записи клиента по номеру телефона.
    Используется при переносе/отмене/повторном звонке.
    """
    ...


# ============= 6. update_booking =============

class UpdateBookingParams(BaseModel):
    booking_id: str = Field(description="ID существующей записи")
    action: str = Field(description="reschedule | update_service | update_master")
    new_start_at: Optional[datetime] = None
    new_service_id: Optional[str] = None
    new_master_id: Optional[str] = None
    reason: Optional[str] = Field(None, description="Причина изменения")

class UpdateBookingResult(BaseModel):
    booking_id: str
    status: str
    summary: str = Field(description="Обновлённое описание записи")
    changes: dict = Field(description="Что изменилось")

async def update_booking(
    tenant_id: str,
    params: UpdateBookingParams,
    booking_service: BookingServiceInterface,
) -> UpdateBookingResult:
    """
    Обновляет существующую запись (перенос, смена услуги/мастера).
    Проверяет конфликты слотов при переносе.
    """
    ...


# ============= 7. cancel_booking =============

class CancelBookingParams(BaseModel):
    booking_id: str = Field(description="ID записи для отмены")
    reason: str = Field(description="Причина: client_request | no_show | other")
    comment: Optional[str] = None

class CancelBookingResult(BaseModel):
    booking_id: str
    status: str = "cancelled"
    cancelled_at: datetime
    penalty_info: Optional[str] = Field(None, description="Информация о штрафе, если применимо")

async def cancel_booking(
    tenant_id: str,
    params: CancelBookingParams,
    booking_service: BookingServiceInterface,
) -> CancelBookingResult:
    """
    Отменяет запись. Если до начала < 2 часов — сообщает о правилах отмены.
    """
    ...


# ============= 8. get_business_info =============

class GetBusinessInfoParams(BaseModel):
    pass

class BusinessInfo(BaseModel):
    name: str
    address: Optional[str] = None
    phone: str
    work_hours: dict
    next_holiday: Optional[date] = None
    description: Optional[str] = None

class GetBusinessInfoResult(BaseModel):
    business: BusinessInfo

async def get_business_info(
    tenant_id: str,
    params: GetBusinessInfoParams,
    booking_service: BookingServiceInterface,
) -> GetBusinessInfoResult:
    """
    Возвращает информацию о салоне (адрес, часы работы, описание).
    """
    ...


# ============= 9. escalate_to_human =============

class EscalateParams(BaseModel):
    call_id: str
    reason: str = Field(description="Причина эскалации: complaint, aggressive, complex_request, other")
    client_summary: Optional[str] = Field(None, description="Краткое описание ситуации для администратора")

class EscalateResult(BaseModel):
    action: str = "transfer"
    forward_to: str = Field(description="Номер для переадресации")
    transfer_initiated: bool

async def escalate_to_human(
    tenant_id: str,
    params: EscalateParams,
    booking_service: BookingServiceInterface,
) -> EscalateResult:
    """
    Эскалация звонка живому человеку.
    Инициирует SIP transfer на номер владельца.
    Если transfer недоступен — обещает перезвонить и ставит задачу.
    """
    ...

# ============= Registry =============

class ToolDef(BaseModel):
    name: str
    description: str
    params_schema: dict       # JSON Schema (Pydantic → JSON Schema)
    returns_schema: dict

TOOL_REGISTRY: dict[str, ToolDef] = {
    "get_services": ToolDef(
        name="get_services",
        description="Получить список услуг салона. Вызывай в начале, чтобы показать клиенту что есть.",
        params_schema=GetServicesParams.model_json_schema(),
        returns_schema=GetServicesResult.model_json_schema(),
    ),
    "get_masters": ToolDef(
        name="get_masters",
        description="Получить список мастеров. Можно отфильтровать по услуге.",
        params_schema=GetMastersParams.model_json_schema(),
        returns_schema=GetMastersResult.model_json_schema(),
    ),
    "find_slots": ToolDef(
        name="find_slots",
        description="Найти свободные слоты на определённую дату.",
        params_schema=FindSlotsParams.model_json_schema(),
        returns_schema=FindSlotsResult.model_json_schema(),
    ),
    "create_booking": ToolDef(
        name="create_booking",
        description="Создать запись клиента на услугу. Вызывай, когда клиент согласился на время.",
        params_schema=CreateBookingParams.model_json_schema(),
        returns_schema=CreateBookingResult.model_json_schema(),
    ),
    "find_booking": ToolDef(
        name="find_booking",
        description="Найти существующие записи клиента по номеру телефона.",
        params_schema=FindBookingParams.model_json_schema(),
        returns_schema=FindBookingResult.model_json_schema(),
    ),
    "update_booking": ToolDef(
        name="update_booking",
        description="Перенести или изменить существующую запись.",
        params_schema=UpdateBookingParams.model_json_schema(),
        returns_schema=UpdateBookingResult.model_json_schema(),
    ),
    "cancel_booking": ToolDef(
        name="cancel_booking",
        description="Отменить запись клиента.",
        params_schema=CancelBookingParams.model_json_schema(),
        returns_schema=CancelBookingResult.model_json_schema(),
    ),
    "get_business_info": ToolDef(
        name="get_business_info",
        description="Получить информацию о салоне (адрес, часы работы).",
        params_schema=GetBusinessInfoParams.model_json_schema(),
        returns_schema=GetBusinessInfoResult.model_json_schema(),
    ),
    "escalate_to_human": ToolDef(
        name="escalate_to_human",
        description="Перевести звонок на администратора. Используй при жалобах, агрессии или сложных запросах.",
        params_schema=EscalateParams.model_json_schema(),
        returns_schema=EscalateResult.model_json_schema(),
    ),
}
```

---

## 5. Realtime voice pipeline

### 5.1 Поток данных

```
SIP → [8 kHz PCM] → VG → [opus] → ASR → [text] → Engine → [text] → TTS → [opus] → VG → SIP

        ┌──────┐     ┌──────────┐     ┌───────────┐     ┌──────────┐     ┌──────┐
        │  SIP  │────▶│   VG     │────▶│   ASR     │────▶│  Engine  │────▶│ TTS  │
        │ Sipuni│     │ pjsua2   │     │ Yandex SK │     │ LLM+Tools│     │ Yand │
        └──────┘     └──────┘   │     └──────────┘     └──────────┘     └──┬───┘
                              │                                            │
                              │     ┌──────────┐                          │
                              └────▶│   VAD    │                          │
                                    │ Silero  │                          │
                                    └──────────┘                          │
                                                                          │
                                                                          ▼
                 ┌─────────────────────────────────────────────────────────┘
                 ▼
            ┌────────┐
            │ Audio  │
            │ Mixer  │
            └────────┘
                 │
                 ▼
              SIP RTP
```

### 5.2 Тайминги

```mermaid
sequenceDiagram
    participant C as Клиент (SIP)
    participant VG as Voice Gateway
    participant ASR as ASR Service
    participant VAD as VAD Service
    participant E as Engine
    participant TTS as TTS Service
    participant LLM as DeepSeek (via OpenClaw)

    Note over C,VG: Звонок поступает (DID → tenant_id)

    VG->>C: 180 Ringing
    VG->>C: 200 OK (SIP ответ)
    VG->>C: ---[аудиопоток RTP]---

    Note over VG,TTS: 🟢 Начало pipeline

    VG->>ASR: [binary audio chunks] (WS stream)
    VG->>VAD: [binary audio chunks] (WS stream)

    Note over C,VG: Клиент: "Здравствуйте, хочу записаться на стрижку"

    VAD-->>VG: speech_start  (0.3s from speech)
    ASR-->>VG: partial: "здравствуйте" (0.5s) [confidence 0.89]
    ASR-->>VG: partial: "здравствуйте хочу записаться" (1.0s)
    ASR-->>VG: final: "здравствуйте хочу записаться на стрижку" (2.0s) [conf 0.95]

    Note over VG,E: 👤 Клиент закончил фразу

    VAD-->>VG: speech_end (0.5s after last speech)

    Note over VG,E: Решение: считать фразу завершённой при:
    Note over VG,E: 1) is_final от ASR + speech_end от VAD
    Note over VG,E: 2) ИЛИ silence > 800ms после промежуточной расшифровки
    Note over VG,E: 3) ИЛИ silence > 3000ms (timeout)

    VG->>E: client_speech {text, is_final: true} (через WS)

    Note over E,LLM: 🔵 Обработка Engine

    E->>E: 1. Идентификация клиента по номеру (+ redis cache)
    E->>E: 2. Сборка system prompt (base + blocks + client context)
    E->>+LLM: POST /api/llm/chat (system + history + user) (stream: true)
    LLM-->>-E: SSE stream: tool_call(get_services)

    E->>E: 3. Выполнение tool_call (вызов Booking через REST)
    E->>E: 4. Передача результата tool обратно в LLM

    LLM-->>E: "Подскажите, на какую дату вы хотите записаться?"
    Note over E,LLM: ⏱ Общее время LLM: ~800ms-1500ms

    Note over E,TTS: 🟡 Параллельная выдача TTS

    E->>TTS: Synthesize("Подскажите, на какую дату вы хотите записаться?")
    TTS-->>E: [audio chunks] (начало через ~300ms)

    Note over VG,TTS: 🟢 Аудио проигрывается клиенту

    E->>VG: ai_response {text, tts_priority: true}
    VG->>C: [TTS audio → RTP]  (первые слова уже звучат)

    Note over C,E: ⏱ Цель: время ответа AI < 2000ms
    Note over C,E: ⏱ Цель: первые слова TTS < 800ms (параллельная выдача)
```

### 5.3 Barge-in (Interrupt) механизм

```mermaid
sequenceDiagram
    participant C as Клиент
    participant VG as Voice Gateway
    participant VAD as VAD Service
    participant TTS as TTS Service
    participant E as Engine

    Note over VG,TTS: AI говорит: "На завтра, 30 апреля, у нас есть..."

    C->>VG: [клиент начинает говорить: "а можно в пятницу?"]
    VAD-->>VG: speech_start!

    Note over VG: 🛑 Interrupt!
    VG->>TTS: Stop synthesis
    VG->>C: Stop RTP audio output
    VG->>E: interrupt_signal {call_id, interrupted_text: "а можно в пятницу?"}

    E->>E: Очищает pending response
    E->>E: Сохраняет контекст (предыдущий диалог сохранён)

    VG->>ASR: continue ASR stream (новая фраза клиента)
    VG->>VAD: continue VAD stream

    Note over E: 🔄 Новый цикл обработки
    Note over E: Важно: контекст диалога сохраняется
```

### 5.4 Pipeline state machine (Voice Gateway)

```
                     ┌──────────┐
                     │  IDLE    │
                     └────┬─────┘
                          │ inbound SIP call
                     ┌────▼─────┐
                     │ RINGING  │
                     └────┬─────┘
                          │ call accepted
                     ┌────▼─────┐
              ┌──────┤ SPEAKING ├──────┐
              │      │ (AI)     │      │
              │      └────┬─────┘      │
              │           │            │
              │    speech_end +        │
              │    silence 800ms       │
              │           │            │
              │      ┌────▼─────┐      │
              └──────┤ LISTENING│      │
              │      │ (client) │      │
              │      └────┬─────┘      │
              │           │            │
              │    speech_start        │
              │    (barge-in)          │
              │           │            │
              └───────────┘            │
                                       │
                                  ┌────▼─────┐
                                  │ESCALATED │
                                  └──────────┘
                                       │
                                  ┌────▼─────┐
                                  │ COMPLETED│
                                  └──────────┘
```

**Переходы:**
- `IDLE → RINGING`: входящий SIP-звонок, определён DID → tenant_id
- `RINGING → SPEAKING`: звонок принят, AI говорит приветствие
- `SPEAKING → LISTENING`: AI закончила фразу, VAD silence 800ms
- `LISTENING → SPEAKING`: ASR финальная расшифровка + VAD speech_end
- `LISTENING → LISTENING`: speech_start (barge-in) — продолжаем слушать
- `* → ESCALATED`: вызов escalate_to_human
- `* → COMPLETED`: успешное завершение диалога
- `* → COMPLETED`: клиент повесил трубку

---

## 6. Multi-tenant изоляция

### 6.1 Уровни изоляции

| Уровень | Механизм | Описание |
|---------|----------|----------|
| **Данные** | `tenant_id` на всех таблицах | Все SQL запросы с `WHERE tenant_id = ?` |
| **SIP** | Индивидуальный DID | Каждый тенант имеет свой номер. Маршрутизация: DID → tenant_id |
| **Redis** | `{tenant_id}:{call_id}:key` | Ключи в Redis с префиксом тенанта |
| **AWS S3** | `{tenant_id}/{date}/{call_id}.opus` | Путь в S3 bucket |
| **LLM** | Отдельный system prompt | Каждый тенант имеет свой prompt_profile |
| **YClients** | Отдельный API-ключ | Каждый тенант подключает свой YClients аккаунт |
| **Admin** | JWT + tenant_id | Авторизация: администратор видит только свой тенант |
| **Лимиты** | rate limiter по tenant_id | Разные квоты на API вызовы |

### 6.2 Row-Level Security (RLS)

Для прямых SQL-запросов через админку используем RLS:

```sql
-- Включаем RLS на tenant-owned таблицах
ALTER TABLE services ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;

-- Политика: видны только строки своего тенанта
CREATE POLICY tenant_isolation ON bookings
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Вспомогательная функция
CREATE OR REPLACE FUNCTION set_tenant_context(p_tenant_id UUID)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', p_tenant_id::TEXT, FALSE);
END;
$$ LANGUAGE plpgsql;
```

### 6.3 API middleware

```python
# shared/middleware/tenant.py

@dataclass
class TenantContext:
    tenant_id: UUID
    name: str
    timezone: str
    settings: TenantSettings

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Извлекает tenant_id из:
    1. Path /api/v1/tenants/{tenant_id}/...
    2. X-Tenant-ID header (для внутренних сервисов)
    3. JWT токена (для admin панели)
    Устанавливает TenantContext в request.state
    """

    async def dispatch(self, request, call_next):
        tenant_id = self._extract_tenant_id(request)
        if not tenant_id:
            return JSONResponse(status_code=401, body={"error": "TENANT_REQUIRED"})

        # Проверяем существование и статус тенанта
        tenant = await tenant_service.get_by_id(tenant_id)
        if not tenant or tenant.status != 'active':
            return JSONResponse(status_code=403, body={"error": "TENANT_INACTIVE"})

        # Устанавливаем контекст
        request.state.tenant = TenantContext(
            tenant_id=tenant.id,
            name=tenant.name,
            timezone=tenant.timezone,
            settings=await tenant_service.get_settings(tenant_id)
        )

        # Устанавливаем tenant_id в SQLAlchemy session
        db_session = request.state.db
        await db_session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, TRUE)"),
            {"tid": str(tenant_id)}
        )

        response = await call_next(request)
        return response
```

---

## 7. Обработка ошибок и graceful degradation

### 7.1 Категории ошибок

```python
# shared/exceptions/errors.py

from enum import Enum

class ErrorCategory(str, Enum):
    # Инфраструктурные
    SIP_UNAVAILABLE = "sip_unavailable"
    DATABASE_UNAVAILABLE = "database_unavailable"
    REDIS_UNAVAILABLE = "redis_unavailable"
    S3_UNAVAILABLE = "s3_unavailable"

    # Внешние сервисы
    YANDEX_ASR_ERROR = "yandex_asr_error"
    YANDEX_TTS_ERROR = "yandex_tts_error"
    DEEPSEEK_ERROR = "deepseek_error"
    YCLIENTS_UNAVAILABLE = "yclients_unavailable"

    # Бизнес-логика
    SLOT_TAKEN = "slot_taken"
    CLIENT_NOT_FOUND = "client_not_found"
    BOOKING_NOT_FOUND = "booking_not_found"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INVALID_TIME = "invalid_time"
    ESALATION_FAILED = "escalation_failed"

    # Security
    UNAUTHORIZED = "unauthorized"
    TENANT_SUSPENDED = "tenant_suspended"
    RATE_LIMITED = "rate_limited"
```

### 7.2 Graceful degradation matrix

| Сценарий | Что ломается | Degradation | Восстановление |
|----------|-------------|-------------|----------------|
| **YClients недоступен** | `create_booking` в YClients | Запись только во внутреннем календаре. Лог: sync_pending. Отложенная синхронизация | Celery retry 3 раза с exponential backoff |
| **YClients недоступен > 1 часа** | Все YClients операции | Внутренний календарь full mode. Алерт владельцу в Telegram | — |
| **DeepSeek недоступен** | `LLM inference` | Retry с backoff (3 попытки). Если все неудачны → fallback: "Извините, технические неполадки, перезвоните позже" | Retry через 30 сек |
| **SIP упал** | Входящие звонки | Звонки идут напрямую владельцу (Sipuni переадресация). Алерт в Telegram | SIP watcher перезапускает pjsua2 |
| **S3 недоступен** | Запись аудио | Отключаем запись. Транскрипт сохраняется в БД. Алерт | Восстановление S3 → отложенная загрузка аудио |
| **Redis недоступен** | Session state | In-memory fallback с TTL. Потеря контекста при рестарте | Восстановление Redis → очистка in-memory |
| **ASR timeout** | Распознавание | После 30 сек тишины: AI спрашивает "Вы здесь?" Ещё 15 сек silence → завершение звонка | — |
| **TTS ошибка** | Синтез речи | Retry 2 раза. Если не удалось → "Извините, техническая ошибка" | — |
| **База недоступна** | Все операции | Read-only mode: AI отвечает "Извините, сервис временно недоступен". Алерт немедленно | PgBouncer переподключение |

### 7.3 Circuit breaker

```python
# shared/utils/circuit_breaker.py

class CircuitBreaker:
    """Circuit breaker для внешних сервисов."""
    
    states: CLOSED, OPEN, HALF_OPEN = "closed", "open", "half_open"

    def __init__(self, name: str, failure_threshold: int = 5,
                 recovery_timeout: int = 30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = self.CLOSED
        self.last_failure_time = None

    async def call(self, fn, *args, **kwargs):
        if self.state == self.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = self.HALF_OPEN
            else:
                raise ServiceUnavailableError(f"{self.name} is OPEN")

        try:
            result = await fn(*args, **kwargs)
            if self.state == self.HALF_OPEN:
                self.state = self.CLOSED
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = self.OPEN
                logger.warning(f"Circuit breaker {self.name} OPEN after "
                              f"{self.failure_count} failures")
            raise e

# Usage
yc_circuit = CircuitBreaker("yclients", failure_threshold=3, recovery_timeout=60)

async def create_booking_in_yclients(...):
    async with yc_circuit:
        return await yclients_api.create_booking(...)
```

### 7.4 Call error handling (для клиента)

```python
# engine/src/dialog/error_handling.py

ERROR_RESPONSES = {
    "service_unavailable": {
        "to_client": "Извините, эта услуга сейчас временно недоступна. "
                     "Могу предложить другие варианты?",
        "action": "suggest_alternatives"
    },
    "slot_taken": {
        "to_client": "К сожалению, это время уже занято. "
                     "У нас есть свободные слоты в {alternatives}. "
                     "Вам какое удобнее?",
        "action": "offer_alternatives"
    },
    "booking_failed": {
        "to_client": "Извините, что-то пошло не так при записи. "
                     "Попробуем ещё раз?",
        "retries": 2
    },
    "escalation_failed": {
        "to_client": "К сожалению, администратор сейчас недоступен. "
                     "Я передала вашу просьбу, вам перезвонят в ближайшее время. "
                     "До свидания!",
        "action": "create_task_for_owner"
    },
    "llm_unavailable": {
        "to_client": "Извините, у нас технические неполадки. "
                     "Пожалуйста, перезвоните позже или напишите нам в Telegram. "
                     "До свидания!",
        "action": "hangup"
    }
}
```

---

## 8. Безопасность

### 8.1 Защита API

| Метод | Где применяется | Детали |
|-------|-----------------|--------|
| **API Key (X-API-Key)** | Внутренние сервисы | Хранятся в Docker secrets. Ротация ежемесячно. |
| **JWT** | Admin Panel | Access token (30 min) + Refresh token (7 days) |
| **HMAC подпись** | Sipuni → Gateway | Проверка webhook подписи Sipuni |
| **TLS** | Все внешние endpoint'ы | Let's Encrypt через reverse proxy |
| **Rate limiting** | Booking API, LLM API | 100 req/min на тенанта. Redis-backed. |
| **IP whitelist** | Internal API | Docker internal network (172.x.x.x) |
| **SQL injection** | All queries | SQLAlchemy ORM (raw SQL запрещён) |

### 8.2 Шифрование

```python
# shared/security/encryption.py

from cryptography.fernet import Fernet
from base64 import b64encode, b64decode

class FieldEncryption:
    """
    Шифрование чувствительных полей в БД.
    Используется для:
    - SIP паролей (sip_settings.sip_password)
    - YClients API-ключей (tenant_settings)
    - API-ключей внутренних сервисов
    """

    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()


# Ключ хранится в Docker secret
# /run/secrets/encryption_key
```

### 8.3 Изоляция тенантов

| Уровень | Механизм |
|---------|----------|
| **Данные** | `tenant_id` на каждой строке + RLS |
| **Сеть** | Каждый сервис в Docker compose с tenant-scoped network |
| **YClients** | Отдельный API-ключ на тенанта, нет shared credentials |
| **SIP** | Индивидуальный DID на тенанта |
| **Admin** | JWT с tenant_id, admin видит только свой салон |
| **Rate limit** | Квота по `tenant_id`, предотвращает DoS одного тенанта другим |

### 8.4 152-ФЗ Compliance

```python
# gateway/src/pipeline/fz152.py

FZ152_DISCLAIMER = "Для контроля качества наш разговор может быть записан."

async def handle_fz152(call: CallContext):
    """
    152-ФЗ: обязательное уведомление о записи разговора.
    - Говорится в начале звонка (сразу после приветствия)
    - Записывается в call.transcript как маркер
    - Хранение аудио 90 дней (удаляется автоматически)
    - Расшифровки хранятся бессрочно
    """
    if not call.fz152_notified:
        await tts_service.speak(call.call_id, FZ152_DISCLAIMER)
        call.fz152_notified = True
        call.transcript_segments.append({
            "speaker": "ai",
            "text": FZ152_DISCLAIMER,
            "type": "fz152_notice"
        })
```

### 8.5 S3 bucket policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::...:role/allo-gateway"
      },
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::allo-audio/*",
      "Condition": {
        "StringLike": {
          "s3:prefix": ["${tenant_id}/*"]
        }
      }
    },
    {
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:DeleteObject",
      "Resource": "arn:aws:s3:::allo-audio/*",
      "Condition": {
        "DateLessThan": {
          "s3:ExistingObjectTag/created_at": "90 days ago"
        }
      }
    },
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::...:role/allo-cleanup"
      },
      "Action": "s3:DeleteObject",
      "Resource": "arn:aws:s3:::allo-audio/*",
      "Condition": {
        "DateLessThan": {
          "s3:ExistingObjectTag/created_at": "90 days ago"
        }
      }
    }
  ]
}
```

---

## 9. Инфраструктурная схема

### 9.1 Docker Compose (MVP)

```yaml
# docker-compose.yml

version: "3.9"

x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"

x-restart: &default-restart
  restart: unless-stopped

services:
  # ===== Reverse Proxy =====
  caddy:
    image: caddy:2
    ports:
      - "80:80"
      - "443:443"
      - "5060:5060/udp"
    volumes:
      - ./infra/caddy/Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - public
      - internal
    <<: *default-restart

  # ===== Databases =====
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: allo
      POSTGRES_USER: allo
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./infra/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    secrets:
      - db_password
    networks:
      - internal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U allo"]
      interval: 10s
      timeout: 5s
      retries: 5
    <<: [*default-restart, *default-logging]

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redisdata:/data
    networks:
      - internal
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    <<: *default-restart

  # ===== Object Storage =====
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD_FILE: /run/secrets/minio_password
    volumes:
      - miniodata:/data
    networks:
      - internal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
    <<: [*default-restart, *default-logging]

  # ===== Voice Gateway (Layer 1) =====
  gateway:
    build:
      context: ./gateway
      dockerfile: Dockerfile
    depends_on:
      redis: { condition: service_healthy }
      postgres: { condition: service_healthy }
    environment:
      DATABASE_URL: postgresql+asyncpg://allo:${DB_PASSWORD}@postgres/allo
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      SPEECH_ASR_URL: ws://speech:8001/ws/asr
      SPEECH_VAD_URL: ws://speech:8001/ws/vad
      ENGINE_URL: ws://engine:8002/ws/dialog
      SIPUNI_API_KEY: ${SIPUNI_API_KEY}
      SIPUNI_ACCOUNT: ${SIPUNI_ACCOUNT}
    networks:
      - internal
    secrets:
      - db_password
    <<: [*default-restart, *default-logging]

  # ===== Speech Services (Layer 2) =====
  speech:
    build:
      context: ./speech
      dockerfile: Dockerfile
    depends_on:
      - redis
    environment:
      YANDEX_API_KEY: ${YANDEX_SPEECHKIT_KEY}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      PORT: 8001
    networks:
      - internal
      - external   # доступ к Yandex API
    secrets:
      - yandex_api_key
    <<: [*default-restart, *default-logging]

  # ===== Conversational Engine (Layer 3) =====
  engine:
    build:
      context: ./engine
      dockerfile: Dockerfile
    depends_on:
      redis: { condition: service_healthy }
      postgres: { condition: service_healthy }
    environment:
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      DATABASE_URL: postgresql+asyncpg://allo:${DB_PASSWORD}@postgres/allo
      OPENCLAW_API_URL: http://openclaw:4000
      OPENCLAW_API_KEY: ${OPENCLAW_API_KEY}
      BOOKING_API_URL: http://booking:8003/api/v1
      SPEECH_TTS_URL: grpc://speech:8002
      PORT: 8002
    networks:
      - internal
    secrets:
      - db_password
      - openclaw_api_key
    <<: [*default-restart, *default-logging]

  # ===== Booking & CRM (Layer 4) =====
  booking:
    build:
      context: ./booking
      dockerfile: Dockerfile
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_healthy }
    environment:
      DATABASE_URL: postgresql+asyncpg://allo:${DB_PASSWORD}@postgres/allo
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      YCLIENTS_BEARER_TOKEN: ${YCLIENTS_BEARER_TOKEN}
      S3_ENDPOINT: http://minio:9000
      S3_ACCESS_KEY: ${MINIO_ROOT_USER}
      S3_SECRET_KEY_FILE: /run/secrets/minio_password
      PORT: 8003
    networks:
      - internal
    secrets:
      - db_password
      - minio_password
    <<: [*default-restart, *default-logging]

  # ===== Celery Worker (async tasks) =====
  celery-worker:
    build:
      context: ./booking
      dockerfile: Dockerfile
    command: celery -A booking.tasks worker --loglevel=info --concurrency=4
    depends_on:
      - redis
      - postgres
      - booking
    environment:
      DATABASE_URL: postgresql+asyncpg://allo:${DB_PASSWORD}@postgres/allo
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      YCLIENTS_BEARER_TOKEN: ${YCLIENTS_BEARER_TOKEN}
    networks:
      - internal
      - external
    secrets:
      - db_password
    <<: [*default-restart, *default-logging]

  celery-beat:
    build:
      context: ./booking
      dockerfile: Dockerfile
    command: celery -A booking.tasks beat --loglevel=info
    depends_on:
      - redis
      - postgres
    environment:
      DATABASE_URL: postgresql+asyncpg://allo:${DB_PASSWORD}@postgres/allo
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
    networks:
      - internal
    secrets:
      - db_password
    <<: *default-restart

  # ===== Admin Panel (Layer 5) =====
  admin:
    build:
      context: ./admin
      dockerfile: Dockerfile
    depends_on:
      - postgres
      - booking
    environment:
      DATABASE_URL: postgresql+asyncpg://allo:${DB_PASSWORD}@postgres/allo
      BOOKING_API_URL: http://booking:8003/api/v1
      JWT_SECRET_FILE: /run/secrets/jwt_secret
      PORT: 8004
    networks:
      - public      # через Caddy
      - internal
    secrets:
      - db_password
      - jwt_secret
    <<: [*default-restart, *default-logging]

  # ===== OpenClaw Gateway =====
  openclaw:
    image: openclaw/openclaw:latest
    depends_on:
      - booking
    environment:
      OPENCLAW_API_KEY: ${OPENCLAW_API_KEY}
    volumes:
      - ./openclaw-plugins:/app/plugins
      - ./infra/openclaw/config.yaml:/app/config.yaml
    ports:
      - "4000:4000"
    networks:
      - internal
    secrets:
      - openclaw_api_key
    <<: *default-restart

networks:
  public:
    driver: bridge
  internal:
    driver: bridge
    internal: true
  external:
    driver: bridge

volumes:
  pgdata:
  redisdata:
  miniodata:
  caddy_data:
  caddy_config:

secrets:
  db_password:
    file: ./secrets/db_password.txt
  minio_password:
    file: ./secrets/minio_password.txt
  openclaw_api_key:
    file: ./secrets/openclaw_api_key.txt
  yandex_api_key:
    file: ./secrets/yandex_api_key.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  encryption_key:
    file: ./secrets/encryption_key.txt
```

### 9.2 Docker Compose override (dev)

```yaml
# docker-compose.override.yml

services:
  postgres:
    ports:
      - "5432:5432"

  redis:
    ports:
      - "6379:6379"

  minio:
    ports:
      - "9000:9000"
      - "9001:9001"

  gateway:
    ports:
      - "8000:8000"       # REST debug
    volumes:
      - ./gateway/src:/app/src

  speech:
    ports:
      - "8001:8001"
    volumes:
      - ./speech/src:/app/src

  engine:
    ports:
      - "8002:8002"
    volumes:
      - ./engine/src:/app/src
      - ./shared:/app/shared

  booking:
    ports:
      - "8003:8003"
    volumes:
      - ./booking/src:/app/src
      - ./shared:/app/shared

  admin:
    ports:
      - "8004:8004"
    volumes:
      - ./admin/src:/app/src
```

### 9.3 Celery tasks (periodic)

```python
# booking/src/tasks.py

from celery import Celery
from celery.schedules import crontab

app = Celery('allo', broker=f'redis://:{REDIS_PASSWORD}@redis:6379/1')

app.conf.beat_schedule = {
    # Напоминания клиентам
    'send_day_reminders': {
        'task': 'booking.tasks.send_reminders',
        'schedule': crontab(hour=9, minute=0),   # каждый день в 9:00
        'kwargs': {'type': 'day_before'}
    },
    'send_hour_reminders': {
        'task': 'booking.tasks.send_reminders',
        'schedule': crontab(minute='*/15'),       # каждые 15 минут
        'kwargs': {'type': 'hour_before'}
    },

    # Очистка
    'cleanup_old_audio': {
        'task': 'booking.tasks.cleanup_old_audio',
        'schedule': crontab(hour=3, minute=0),    # каждый день в 3:00
    },
    'cleanup_expired_sessions': {
        'task': 'booking.tasks.cleanup_redis_sessions',
        'schedule': crontab(hour=4, minute=0),
    },

    # Синхронизация
    'sync_yclients_pending': {
        'task': 'booking.tasks.sync_pending_bookings',
        'schedule': crontab(minute='*/5'),        # каждые 5 минут
    },

    # Мониторинг
    'health_check_yclients': {
        'task': 'monitoring.tasks.check_yclients_health',
        'schedule': crontab(minute='*/10'),
    },
}

@app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_reminders(self, type: str):
    """Отправка SMS и Telegram напоминаний."""
    # Выборка scheduled_notifications где send_at <= now AND sent = false
    # Для каждого: отправка SMS/TG, отметка sent = true
    ...

@app.task(bind=True)
def cleanup_old_audio(self):
    """Удаление аудио старше 90 дней из S3."""
    ...
```

---

## 10. OpenClaw интеграция

### 10.1 Архитектура связки

```
┌────────────────────────────────────────────────────────────────┐
│                    Conversational Engine (Python)                │
│                                                                  │
│  ┌───────────────────┐    ┌─────────────────────────────────┐   │
│  │  Dialog Manager    │───▶│  Tool Executor                  │   │
│  │  (asyncio)         │    │                                 │   │
│  └───────────────────┘    │  get_services() → HTTP POST     │   │
│                            │       → OpenClaw Plugin        │   │
│                            │       → Python Tool Library    │   │
│                            │       → Booking Service        │   │
│                            │                                 │   │
│                            │  escalate_to_human() → HTTP    │   │
│                            │       → Voice Gateway API      │   │
│                            └─────────────────────────────────┘   │
│                                                                  │
│  ┌───────────────────┐    ┌─────────────────────────────────┐   │
│  │  LLM Client        │───▶│  OpenClaw REST API             │   │
│  │  (HTTP/SSE)        │    │  POST /api/llm/chat            │   │
│  └───────────────────┘    └───────────┬─────────────────────┘   │
└──────────────────────────────────────┼─────────────────────────┘
                                       │
                              ┌────────▼──────────────────────┐
                              │     OpenClaw Gateway (TS)      │
                              │                                │
                              │  ┌────────────────────────┐   │
                              │  │  LLM Proxy              │   │
                              │  │  DeepSeek-v4-flash      │   │
                              │  └────────────────────────┘   │
                              │                                │
                              │  ┌────────────────────────┐   │
                              │  │  Telegram Bot Plugin    │   │
                              │  │  (текстовые уведомл.)  │   │
                              │  └────────────────────────┘   │
                              │                                │
                              │  ┌────────────────────────┐   │
                              │  │  Booking Plugin (TS)    │   │
                              │  │  → REST → Python tools  │   │
                              │  └────────────────────────┘   │
                              │                                │
                              │  ┌────────────────────────┐   │
                              │  │  Calendar Plugin (TS)   │   │
                              │  │  → REST → Python tools  │   │
                              │  └────────────────────────┘   │
                              │                                │
                              │  ┌────────────────────────┐   │
                              │  │  Masters Plugin (TS)    │   │
                              │  │  → REST → Python tools  │   │
                              │  └────────────────────────┘   │
                              └────────────────────────────────┘
```

### 10.2 Engine → OpenClaw LLM API

```python
# engine/src/llm/openclaw_client.py

from httpx import AsyncClient, AsyncHTTPTransport
from sse_starlette.sse import ServerSentEvent

class OpenClawLLMClient:
    """
    Клиент к OpenClaw для LLM inference.
    OpenClaw выступает как прокси к DeepSeek API.
    """

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }
        self.client = AsyncClient(
            transport=AsyncHTTPTransport(retries=2),
            timeout=30.0,
        )

    async def chat_stream(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> AsyncGenerator[LLMChunk, None]:
        """
        Streaming chat completion через OpenClaw.
        Возвращает SSE-поток с событиями:
        - message: текст ответа
        - tool_call: информация о вызове инструмента
        - done: завершение
        """
        payload = {
            "model": "deepseek/deepseek-v4-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages,
            ],
            "tools": tools,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/llm/chat",
            json=payload,
            headers=self.headers,
        ) as response:
            if response.status_code != 200:
                error_body = await response.aread()
                raise LLMError(
                    status=response.status_code,
                    detail=error_body.decode(),
                )

            async for line in response.aiter_lines():
                if line.startswith("event: "):
                    event_type = line[7:].strip()
                elif line.startswith("data: "):
                    data = json.loads(line[6:])
                    yield LLMChunk(event=event_type, data=data)
```

### 10.3 OpenClaw TS Plugin — Booking (wrapper)

```typescript
// openclaw-plugins/booking-plugin/index.ts

import { OpenClawPlugin, PluginEvent, PluginResponse } from '@openclaw/sdk';

interface BookingServiceConfig {
  apiUrl: string;      // http://booking:8003/api/v1
  apiKey: string;
}

export class BookingPlugin extends OpenClawPlugin {
  private config: BookingServiceConfig;

  constructor(config: BookingServiceConfig) {
    super('booking');
    this.config = config;
  }

  async onEvent(event: PluginEvent): Promise<PluginResponse> {
    // OpenClaw routing: HTTP POST from Engine → this handler
    const { tool, params, tenant_id } = event.payload;

    // Проксируем вызов в Python Booking Service
    const response = await fetch(
      `${this.config.apiUrl}/tenants/${tenant_id}/${tool}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Internal-API-Key': this.config.apiKey,
        },
        body: JSON.stringify(params),
      }
    );

    if (!response.ok) {
      return { error: await response.json() };
    }

    const data = await response.json();
    return { success: true, data };
  }
}

// Регистрация плагина
export default function createPlugin(config: BookingServiceConfig) {
  return new BookingPlugin(config);
}
```

### 10.4 OpenClaw plugin routing config

```yaml
# infra/openclaw/config.yaml

plugins:
  - name: booking
    path: /app/plugins/booking-plugin
    config:
      apiUrl: http://booking:8003/api/v1
      apiKey: ${BOOKING_API_KEY}
    routes:
      - method: POST
        path: /api/v1/tools/booking/get-services
        handler: get_services
      - method: POST
        path: /api/v1/tools/booking/create-booking
        handler: create_booking
      - method: POST
        path: /api/v1/tools/booking/find-booking
        handler: find_booking
      - method: POST
        path: /api/v1/tools/booking/update-booking
        handler: update_booking
      - method: POST
        path: /api/v1/tools/booking/cancel-booking
        handler: cancel_booking

  - name: calendar
    path: /app/plugins/calendar-plugin
    config:
      apiUrl: http://booking:8003/api/v1
      apiKey: ${BOOKING_API_KEY}
    routes:
      - method: POST
        path: /api/v1/tools/calendar/find-slots
        handler: find_slots

  - name: masters
    path: /app/plugins/masters-plugin
    config:
      apiUrl: http://booking:8003/api/v1
      apiKey: ${BOOKING_API_KEY}
    routes:
      - method: POST
        path: /api/v1/tools/masters/get-masters
        handler: get_masters
      - method: POST
        path: /api/v1/tools/masters/get-business-info
        handler: get_business_info
      - method: POST
        path: /api/v1/tools/masters/escalate
        handler: escalate_to_human

  - name: telegram-bot
    path: /app/plugins/telegram-bot
    config:
      botToken: ${TELEGRAM_BOT_TOKEN}
      webhookUrl: https://allo.example.com/webhooks/telegram
```

### 10.5 Engine → Python Tool Library (direct call flow)

Когда Engine вызывает tool **без OpenClaw** (для скорости):

```python
# engine/src/tools/executor.py

from shared.tools import get_services, create_booking, TOOL_REGISTRY

class ToolExecutor:
    """
    Исполнитель tool-вызовов от LLM.
    
    Два режима:
    1. Быстрый (default): прямой вызов Python tool library.
       Только для инструментов, не требующих OpenClaw.
    2. Через OpenClaw: для инструментов, требующих OpenClaw-плагинов
       (взаимодействие с Telegram, внешние системы через OpenClaw).
    """

    def __init__(self, booking_api_url: str, openclaw_client: OpenClawLLMClient):
        self.booking_client = BookingServiceClient(booking_api_url)
        self.openclaw = openclaw_client

    # Инструменты, работающие через Python → HTTP → Booking Service
    # (быстрый путь, без OpenClaw)
    TOOL_ROUTING = {
        "get_services":     ("python", get_services),
        "get_masters":      ("python", get_masters),
        "find_slots":       ("python", find_slots),
        "create_booking":   ("python", create_booking),
        "find_booking":     ("python", find_booking),
        "update_booking":   ("python", update_booking),
        "cancel_booking":   ("python", cancel_booking),
        "get_business_info":("python", get_business_info),
        "escalate_to_human":("openclaw", "escalate"),  # требует OpenClaw
    }

    async def execute(
        self,
        tool_name: str,
        args: dict,
        tenant_id: str,
    ) -> dict:
        routing = self.TOOL_ROUTING.get(tool_name)
        if not routing:
            raise UnknownToolError(f"Unknown tool: {tool_name}")

        mode, target = routing

        if mode == "python":
            # Прямой вызов Python функции с DI
            tool_fn = target
            result = await tool_fn(
                tenant_id=tenant_id,
                params=tool_fn.ParamsModel(**args),
                booking_service=self.booking_client,
            )
            return result.model_dump(mode='json')

        elif mode == "openclaw":
            # Вызов через OpenClaw TS plugin
            oc_tool, oc_params = self._translate_to_openclaw(tool_name, args)
            result = await self.openclaw.call_tool(
                tool=oc_tool,
                params=oc_params,
                tenant_id=tenant_id,
            )
            return result
```

### 10.6 Telegram Bot (через OpenClaw)

```python
# notifications/src/telegram/handler.py

class TelegramNotificationHandler:
    """
    Отправка уведомлений владельцу через OpenClaw Telegram Bot.
    OpenClaw управляет Telegram Bot, мы шлём ему команды.
    """

    async def send_booking_notification(
        self,
        tenant_id: str,
        booking: BookingInfo,
    ):
        await self.openclaw.call_tool(
            tool="telegram_send",
            params={
                "chat_id": booking.owner_telegram_chat_id,
                "text": (
                    f"✅ Новая запись!\n"
                    f"🕐 {booking.start_at.strftime('%d.%m %H:%M')}\n"
                    f"👤 {booking.client_name}\n"
                    f"💇 {booking.service_name}\n"
                    f"✂️ {booking.master_name}\n"
                    f"💰 {booking.price_rub} ₽"
                ),
            }
        )

    async def send_escalation_notification(
        self,
        tenant_id: str,
        escalation: EscalationInfo,
    ):
        await self.openclaw.call_tool(
            tool="telegram_send",
            params={
                "chat_id": escalation.owner_chat_id,
                "text": (
                    f"🚨 Эскалация звонка!\n"
                    f"📞 Клиент: {escalation.client_phone}\n"
                    f"❓ Причина: {escalation.reason}\n"
                    f"📝 {escalation.summary}"
                ),
                "buttons": [
                    {"text": "Перезвонить клиенту", "callback_data": "call_back"},
                    {"text": "Детали звонка", "url": escalation.call_detail_url},
                ]
            }
        )
```

### 10.7 Границы OpenClaw

| Функция | Через OpenClaw? | Почему |
|---------|----------------|--------|
| **LLM inference** (DeepSeek) | ✅ Да | OpenClaw управляет моделями |
| **Telegram Bot** | ✅ Да | OpenClaw — нативный Telegram клиент |
| **Tools → Booking** | ❌ Нет (Python прямой) | Дополнительный hop без пользы |
| **Tools → YClients** | ❌ Нет (Python модуль) | Прямая интеграция в Booking Service |
| **Tools → SIP/Escalation** | ✅ Да | OpenClaw как оркестратор |
| **Admin кэш/редиректы** | ❌ Нет | Чистый Python/FastAPI |
| **WhatsApp v2** | ✅ Да (future) | OpenClaw канал |

---

## Приложение A: Complexity Estimate

| Компонент | Story Points | Команда | Зависимости |
|-----------|:-----------:|---------|-------------|
| **S1** Project skeleton | 3 | 1 backend | — |
| **S2** DB schema + migrations | 5 | 1 backend | S1 |
| **S3** Tools library | 8 | 1 backend | S2 |
| **S4** Yandex ASR | 8 | 2 backend (интеграция) | S1 |
| **S5** Yandex TTS | 5 | 1 backend | S1 |
| **S6** VAD integration | 5 | 1 backend | S1 |
| **S7** Sipuni inbound | 8 | 2 backend (телефония) | S4, S6 |
| **S8** Sipuni transfer | 5 | 1 backend | S7 |
| **S9** Voice pipeline E2E | 13 | 2 backend | S4-S8 |
| **S10** Prompt — booking flow | 8 | 1 backend (LLM) | S3 |
| **S11** Prompt — edge cases | 8 | 1 backend (LLM) | S10 |
| **S12** Dialog state (Redis) | 5 | 1 backend | S1 |
| **S13** Anti-hallucination | 8 | 1 backend (LLM) | S10 |
| **S14** Internal calendar | 8 | 1 backend | S2 |
| **S15** YClients integration | 8 | 2 backend | S2, S14 |
| **S16** Client database | 5 | 1 backend | S2 |
| **S17** Admin wizard | 8 | 1 fullstack | S2 |
| **S18** Admin dashboard | 5 | 1 fullstack | S2 |
| **S19** Telegram bot | 5 | 1 backend | S3, OSS |
| **S20** SMS reminders | 5 | 1 backend | S2, S7 |
| **S21** Engine tests | 8 | 1 backend | S10-S13 |
| **S22** Booking tests | 5 | 1 backend | S14-S16 |
| **S23** E2E tests | 8 | 1 QA + 1 backend | S9, S15 |
| **S24** Documentation | 3 | 1 tech writer | All |
| **Итого** | **152** | — | — |

**Риски (добавочные SP):**
- Настройка Yandex SpeechKit для телефонии (8 kHz): +3 SP
- Sipuni дебаг в production: +5 SP
- Anti-hallucination regression suite: +3 SP

## Приложение B: Risks & Open Questions

### Известные риски

| Риск | Impact | Вероятность | Mitigation |
|------|--------|:----------:|------------|
| Yandex SpeechKit latency в пике | Средний | 30% | Кэширование голосовых фраз, fallback на предзаписанные сообщения |
| Sipuni WebSocket stability | Высокий | 20% | Heartbeat, auto-reconnect, graceful switch к direct forwarding |
| DeepSeek v4 flash hallucinations | Средний | 15% | Anti-hallucination guards, regression tests, validation layer |
| YClients rate limits | Средний | 40% | Кэширование справочников, queue-based создание записей |
| Network latency: SIP → ASR → LLM → TTS | Высокий | 25% | TTS parallel streaming, aggressive VAD timeout tuning |
| 152-ФЗ compliance при масштабировании | Низкий | 10% | Вшито в pipeline, аудит 90-дневного удаления |
| Конкуренция слотов (2 одновременных звонка) | Средний | 30% | Optimistic locking + retry, уведомление второго клиента |

### Open questions

1. **Масштабирование pjsua2:** один процесс pjsua2 обрабатывает ~50 параллельных звонков. Как масштабировать на 500+? (Вариант: несколько gateway инстансов с Sipuni балансировкой)
2. **YClients sync conflicts:** что делать, если запись создана во внутреннем календаре, но YClients вернул 409 Conflict? (Предварительно: retry + уведомление админу)
3. **DeepSeek cost при масштабировании:** ~$0.15/1M input tokens. При 500 звонках/день × 2K токенов = ~$0.15/день. При 10K звонках = ~$3/день. Нужен мониторинг cost.
4. **Telegram Bot vs WhatsApp v2:** WhatsApp указан как "v2". Когда внедрять? Какой провайдер?
5. **SMS провайдер:** Sipuni SMS для MVP. Нужна альтернатива при масштабировании?

## Приложение C: Cost Estimate (monthly, MVP)

| Сервис | Цена | Примечание |
|--------|:----:|------------|
| **VPS (Hetzner CX31)** | €5.99 | 4 vCPU, 8 GB RAM, 80 GB NVMe |
| **PostgreSQL** | входит в VPS | — |
| **Redis** | входит в VPS | — |
| **MinIO** | входит в VPS | 80 GB = ~900 звонков по 5 мин (@60 MB/мин) |
| **Sipuni** | 0–500 ₽/мес | 1 номер 200 ₽ + минуты (~300 мин/мес) |
| **Yandex SpeechKit ASR** | ~500 ₽/мес | ~8 часов аудио (расчёт: 300 звонков по 1.5 мин) |
| **Yandex SpeechKit TTS** | ~300 ₽/мес | ~4 часа синтеза |
| **DeepSeek API** | ~$4.50 | ~500 звонков/месяц |
| **YClients** | Бесплатно | Базовый тариф |
| **SMS (Sipuni)** | ~1 ₽/SMS | 1000 SMS/месяц = ~1000 ₽ |
| **Итого (MVP)** | **~2500 ₽/мес** | ≈ $28/мес |

---

*Архитектура утверждена. Изменения — через DECISIONS.md.*
