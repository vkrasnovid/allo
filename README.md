# Алло — голосовой AI-секретарь для сферы услуг

> Принимает звонки, записывает клиентов, ничего не забывает.

**Алло** — это голосовой AI-секретарь для салонов красоты, барбершопов, стоматологий и любых сервисных бизнесов. Алло отвечает на входящие звонки, ведёт естественный диалог с клиентом, подбирает свободное время, создаёт запись и отправляет уведомления владельцу — без участия человека.

Система построена на пяти независимых слоях (Python/FastAPI + PostgreSQL + Redis), использует Yandex SpeechKit для голоса и DeepSeek для понимания диалога.

---

## Содержание

- [Как это работает](#как-это-работает)
- [Архитектура](#архитектура)
- [Быстрый старт](#быстрый-старт)
- [Сервисы](#сервисы)
- [Технологический стек](#технологический-стек)
- [Переменные окружения](#переменные-окружения)
- [API документация](#api-документация)
- [Развёртывание](#развёртывание)
- [Часто задаваемые вопросы](#часто-задаваемые-вопросы)
- [Лицензия](#лицензия)

---

## Как это работает

```
Клиент звонит → Алло отвечает → Определяет салон → Диалог → Запись → Уведомление
```

1. Клиент набирает номер салона
2. Алло отвечает голосом и представляется
3. Распознаёт речь (Yandex SpeechKit ASR)
4. Понимает запрос (DeepSeek через кастомный промпт)
5. Проверяет доступность мастеров и свободные слоты
6. Создаёт запись во внутреннем календаре и YClients
7. Отправляет уведомление владельцу в Telegram
8. Напоминает клиенту о визите по SMS

В сложных случаях (жалобы, агрессия) — переводит звонок на владельца.

---

## Архитектура

Подробная архитектура — в [ARCHITECTURE.md](./ARCHITECTURE.md). Краткая схема:

```
Внешний мир                    Внутренние сервисы
┌──────────┐    SIP/RTP    ┌──────────────┐    WS    ┌──────────┐
│  Sipuni   │◄────────────►│  Gateway      │◄───────►│  Speech  │
│ (телефония)│             │ (pjsua2)     │         │ (ASR,TTS)│
└──────────┘               └──────┬───────┘         └──────────┘
                                  │ WS
                           ┌──────▼───────┐    REST    ┌──────────┐
                           │  Engine       │◄─────────►│  Booking │
                           │ (LLM + Tools) │           │ (CRM)    │
                           └──────┬───────┘           └────┬─────┘
                                  │                        │
                          OpenClaw│                 ┌──────▼──────┐
                           ┌──────▼───────┐         │ PostgreSQL  │
                           │  Admin Panel  │         │ + Redis     │
                           │  + TG Bot     │         └─────────────┘
                           └──────────────┘
```

**Пять слоёв:**

| Слой | Сервис | Назначение |
|------|--------|------------|
| 1 — Voice Gateway | `gateway/` | SIP-телефония, аудиопотоки, состояние звонка |
| 2 — Speech Layer | `speech/` | Распознавание (ASR) и синтез (TTS) речи |
| 3 — Engine | `engine/` | Диалог, LLM, вызов инструментов |
| 4 — Booking & CRM | `booking/` | Календарь, запись, YClients |
| 5 — Admin & Notifications | `admin/`, `notifications/` | Панель управления, Telegram, SMS |

---

## Быстрый старт

### Требования

- Docker и Docker Compose (v2.22+)
- Make
- 4 vCPU, 8 GB RAM (рекомендуется)
- API-ключи: Yandex SpeechKit, DeepSeek (через OpenClaw), Sipuni

### Запуск

```bash
# 1. Клонировать репозиторий
git clone git@github.com:vkrasnovid/allo.git
cd allo

# 2. Настроить переменные окружения
cp .env.example .env
# Отредактируйте .env — добавьте API-ключи

# 3. Создать secrets (пароли для сервисов)
mkdir -p secrets
echo "your_db_password" > secrets/db_password.txt
echo "your_minio_password" > secrets/minio_password.txt
echo "your_openclaw_key" > secrets/openclaw_api_key.txt
echo "your_yandex_key" > secrets/yandex_api_key.txt
echo "your_jwt_secret" > secrets/jwt_secret.txt
echo "your_encryption_key" > secrets/encryption_key.txt

# 4. Запустить все сервисы
docker compose up -d

# 5. Прогнать миграции
make migrate

# 6. Залить seed-данные
make seed
```

После запуска:

| Сервис | Адрес |
|--------|-------|
| Admin Panel | `http://localhost:8004` |
| Booking API | `http://localhost:8003` |
| OpenClaw | `http://localhost:4000` |
| MinIO Console | `http://localhost:9001` |

### Проверка

```bash
# Проверить, что Booking API отвечает
curl http://localhost:8003/api/v1/tenants/health

# Проверить Admin Panel
open http://localhost:8004

# Посмотреть логи Engine
docker compose logs -f engine
```

---

## Сервисы

### Gateway (`gateway/`) — Voice Gateway

Принимает входящие SIP-звонки через Sipuni, управляет аудиопотоками (opus/PCM), координирует ASR → Engine → TTS пайплайн. Реализует state machine для этапов звонка (IDLE → RINGING → SPEAKING → LISTENING → COMPLETED) и barge-in (прерывание AI клиентом).

- **Port:** 8000 (debug REST), SIP: 5060/UDP
- **Stack:** FastAPI, pjsua2
- **WebSocket:** `/ws/dialog/{call_id}` (для Engine)

### Speech (`speech/`) — Speech Services

Два основных модуля: ASR (Yandex SpeechKit streaming-распознавание) и TTS (Yandex SpeechKit streaming-синтез), а также VAD (Silero VAD для определения голосовой активности).

- **Port:** 8001
- **Stack:** FastAPI, Silero VAD, Yandex SpeechKit gRPC
- **WebSocket:** `/ws/asr/{call_id}`, `/ws/vad/{call_id}`
- **gRPC:** TTS stream

### Engine (`engine/`) — Conversational Engine

Управляет диалогом: собирает system prompt из блоков, вызывает DeepSeek через OpenClaw LLM-proxy, исполняет tool-вызовы (через Python Tool Library напрямую), управляет состоянием сессии в Redis.

- **Port:** 8002
- **Stack:** FastAPI, asyncio, Redis
- **WebSocket:** `/ws/dialog/{call_id}` (от Gateway)

### Booking (`booking/`) — Booking & CRM

Внутренний календарь, CRUD записей, клиентская база, YClients-адаптер. Celery worker для отложенных задач (напоминания, синхронизация, очистка аудио).

- **Port:** 8003
- **Stack:** FastAPI, SQLAlchemy 2, Alembic, Celery
- **DB:** PostgreSQL 15

### Admin (`admin/`) — Admin Panel

Веб-интерфейс для владельца салона: дашборд со статистикой, история звонков (с плеером и расшифровкой), список записей, настройки (SIP, YClients, промпт), онбординг-визард.

- **Port:** 8004
- **Stack:** FastAPI, Jinja2, HTMX
- **Auth:** JWT (access + refresh)

### Notifications (`notifications/`) — Notifications

SMS-напоминания (Sipuni SMS) и Telegram-бот для владельца.

- **Stack:** Celery tasks, Sipuni SMS API, OpenClaw Telegram Bot

### Shared (`shared/`) — Shared Code

Общие модули: Python Tool Library (9 инструментов для Engine), Pydantic-модели, иерархия ошибок, tenant-мидлварь, circuit breaker, утилиты.

- **Язык:** Python
- **Tools:** `get_services`, `get_masters`, `find_slots`, `create_booking`, `find_booking`, `update_booking`, `cancel_booking`, `get_business_info`, `escalate_to_human`

---

## Технологический стек

| Компонент | Технология | Назначение |
|-----------|-----------|------------|
| **Backend (Python)** | FastAPI + Pydantic v2 | Все сервисы |
| **Database** | PostgreSQL 15 | Основное хранилище |
| **Cache / State** | Redis 7 | Сессии, кэш, Celery broker |
| **Object Storage** | MinIO / S3 | Аудиозаписи звонков |
| **ASR** | Yandex SpeechKit | Распознавание речи |
| **TTS** | Yandex SpeechKit | Синтез речи |
| **VAD** | Silero VAD | Голосовая активность |
| **LLM** | DeepSeek v4-flash (через OpenClaw) | Понимание диалога |
| **Telephony** | pjsua2 + Sipuni API | SIP-звонки |
| **Async Tasks** | Celery + Redis | Напоминания, очистка |
| **Reverse Proxy** | Caddy 2 | TLS, маршрутизация |
| **OpenClaw** | OpenClaw Gateway | LLM-proxy, Telegram Bot, TS-плагины |
| **Admin Panel** | Jinja2 + HTMX | Веб-интерфейс владельца |
| **CI/CD** | GitHub Actions | Тесты, деплой |
| **Migrations** | Alembic | Схема БД |

---

## Переменные окружения

Основные переменные в `.env`:

| Переменная | Обязательная | Описание |
|-----------|:----------:|----------|
| `DB_PASSWORD` | ✅ | Пароль к PostgreSQL |
| `REDIS_PASSWORD` | ✅ | Пароль к Redis |
| `SIPUNI_API_KEY` | ✅ | API-ключ Sipuni |
| `SIPUNI_ACCOUNT` | ✅ | Аккаунт Sipuni |
| `YANDEX_SPEECHKIT_KEY` | ✅ | API-ключ Yandex SpeechKit |
| `OPENCLAW_API_KEY` | ✅ | Ключ для OpenClaw Gateway |
| `YCLIENTS_BEARER_TOKEN` | ✅ | Токен YClients |
| `TELEGRAM_BOT_TOKEN` | ✅ | Токен Telegram-бота |
| `MINIO_ROOT_USER` | ✅ | Пользователь MinIO |
| `JWT_SECRET` | ✅ | Секрет для JWT |
| `ENCRYPTION_KEY` | ✅ | Ключ шифрования полей |

Полный список — в `.env.example`.

---

## API документация

- [API.md](./API.md) — полная спецификация API (Booking Service, Engine, Speech, Gateway)
- `http://localhost:8003/docs` — Swagger Booking API (в dev-режиме)
- `http://localhost:8004/docs` — Swagger Admin API (в dev-режиме)

---

## Развёртывание

См. [DEPLOYMENT.md](./DEPLOYMENT.md) — продакшн-деплой, мониторинг, backup.

### MVP инфраструктура

| Ресурс | Конфигурация |
|--------|-------------|
| VPS | Hetzner CX31 (4 vCPU, 8 GB, 80 GB NVMe) |
| DB | PostgreSQL 15 (в контейнере) |
| Cache | Redis 7 (в контейнере) |
| Storage | MinIO (80 GB, ~900 звонков × 5 мин) |
| Стоимость | ~2500 ₽/мес ($28) |

---

## Часто задаваемые вопросы

### Для владельца салона

**Как Алло подключается к моему номеру?**
Вы получаете новый SIP-номер (DID) в Алло и настраиваете переадресацию со своего текущего номера. Весь процесс занимает около 30 минут через мастер настройки.

**Что если клиент не хочет записываться?**
Алло спросит один раз и попрощается. Никаких уговоров.

**А если клиент жалуется?**
Алло переведёт звонок на вас в реальном времени. Вы получите уведомление в Telegram.

**Что если YClients недоступен?**
Запись создаётся во внутреннем календаре. Когда YClients восстановится, данные синхронизируются автоматически.

### Для разработчика

**Какие API-ключи нужны для локальной разработки?**
Yandex SpeechKit (ASR + TTS), DeepSeek (через OpenClaw), Sipuni (телефония). Подробнее — в `.env.example`.

**Как запустить только один сервис?**
```bash
docker compose up -d postgres redis  # зависимости
docker compose up -d booking         # целевой сервис
```

**Где тестовые данные?**
`make seed` создаёт тестовый салон «Салон красоты Элегант» с услугами, мастерами и настройками.

---

## Лицензия

Проприетарная. Все права защищены.

---

*Документация для технических специалистов и владельцев бизнеса. По вопросам — dreamteam-bot@openclaw.local.*
