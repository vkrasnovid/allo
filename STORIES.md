# TASK-026: Алло — Голосовой AI-секретарь для сферы услуг

## Decisions (human approved)
1. **OpenClaw границы:** только текстовые каналы (Telegram-бот владельца + WhatsApp v2). Голосовой движок — отдельный сервис. Tools → Python-библиотека, OpenClaw-плагины → TS-обёртки через REST.
2. **Хранение звонков:** аудио 90 дней (S3/MinIO) + расшифровки бессрочно. Шифрование at-rest. 152-ФЗ: фраза в приветствии.
3. **"Просто спросить":** ответ + одно предложение записи. Отказ → прощание. Жёсткое правило в промпте.
4. **SIP-номера:** индивидуальный DID на тенанта. Клиент ставит переадресацию. Маршрутизация по DID → tenant_id.
5. **Промпты:** базовый промпт + конфигурируемые блоки на тенанта. В БД prompt_profile (MVP: только beauty_salon).

## Stories

### EPIC 1: Foundation (S1-S3)

#### S1: Project Skeleton & Monorepo
- Структура: `gateway/`, `speech/`, `engine/`, `booking/`, `admin/`, `notifications/`, `shared/`
- Docker Compose: PostgreSQL 15, Redis, заглушки для внешних сервисов
- Базовая схема БД: tenants, services, masters, bookings, clients, calls, prompt_profiles
- CI: GitHub Actions (lint, test)
- Acceptance: `docker compose up` поднимает все сервисы, миграции прогоняются

#### S2: Database Schema & Migrations
- Полная схема с tenant_id на всех таблицах
- Alembic миграции
- Модели SQLAlchemy 2 + Pydantic v2 схемы
- Seed-данные для тестового салона
- Acceptance: миграции накатываются, seed создаёт тестовый салон с услугами и мастерами

#### S3: Shared Tools Library
- Python-библиотека tools в `shared/tools/`
- 9 tools: get_services, get_masters, find_slots, create_booking, find_booking, update_booking, cancel_booking, get_business_info, escalate_to_human
- Интерфейс: чистые функции с DI для тестирования
- Acceptance: все 9 tools импортируются и работают на mock-данных

### EPIC 2: Speech Layer (S4-S6)

#### S4: Yandex SpeechKit ASR Integration
- Streaming распознавание речи (gRPC/WS)
- Настройка под телефонию (8 кГц)
- Custom vocabulary с названиями услуг салона
- Acceptance: подаём тестовый wav → получаем корректную русскую расшифровку

#### S5: Yandex SpeechKit TTS Integration
- Streaming синтез речи (голоса Алёна/Ермил)
- Параллельная выдача: первые слова отдаются пока LLM генерирует продолжение
- Acceptance: подаём текст → получаем аудиофайл с естественным голосом

#### S6: Voice Activity Detection (VAD)
- Silero VAD: определение конца фразы клиента
- Определение начала речи (для interrupt-механизма)
- Acceptance: на тестовой записи диалога VAD корректно сегментирует фразы

### EPIC 3: Voice Gateway (S7-S9)

#### S7: Sipuni Integration — Inbound Calls
- Приём входящего SIP-звонка через Sipuni API
- Извлечение DID (определение тенанта)
- Передача аудиопотока в Speech Layer
- Acceptance: звонок на тестовый номер → AI отвечает голосом

#### S8: Sipuni Integration — Call Transfer
- Перевод звонка на номер владельца (эскалация)
- Callback-запись если владелец недоступен
- Acceptance: AI переводит звонок на указанный номер

#### S9: Voice Pipeline E2E
- Связка: SIP → ASR → Engine → TTS → SIP
- Обработка прерываний (interrupt)
- Graceful degradation: если SIP сломался — звонки идут напрямую владельцу
- Acceptance: полный диалог записи на услугу через тестовый номер

### EPIC 4: Conversational Engine (S10-S13)

#### S10: Prompt Engineering — Booking Flow
- Базовый промпт с конфигурируемыми блоками (название, тон, приветствие)
- Tools integration: модель вызывает tools, не выдумывает данные
- Разговорный стиль: короткие фразы, "ага", "минутку", без причастий
- Acceptance: текстовый диалог записи (без голоса) проходит корректно

#### S11: Prompt Engineering — Edge Cases
- Сценарий "просто спросить" (одно предложение записи)
- Сценарий переноса/отмены
- Эскалация при жалобах/хамстве
- Acceptance: все сценарии проходят в текстовых тестах

#### S12: Dialogue State Management
- Redis: контекст диалога (TTL = длительность + 1 час)
- История сообщений для multi-turn
- Изоляция по tenant_id + call_id
- Acceptance: повторный звонок находит предыдущий контекст

#### S13: Anti-Hallucination Guards
- Валидация: все числа, имена, цены — только из tool outputs
- Регрессионные тесты на каждое изменение промпта
- Логирование случаев когда модель пыталась выдумать данные
- Acceptance: 100 тестовых диалогов, 0 галлюцинаций в ценах/именах

### EPIC 5: Booking & CRM (S14-S16)

#### S14: Internal Calendar
- PostgreSQL: слоты, проверка конфликтов, использование квот YClients
- API: CRUD записей с валидацией
- Acceptance: создание записи без конфликтов

#### S15: YClients Integration
- Адаптер YClients API: чтение услуг, мастеров, записей
- Кэширование справочников (1 запрос при старте звонка)
- Создание/обновление записей в YClients
- Graceful handling: если YClients недоступен → fallback на внутренний календарь
- Acceptance: звонок → запись создана в YClients, видна в их интерфейсе

#### S16: Client Database
- Клиенты: телефон → история визитов, предпочтения
- Идентификация по номеру телефона при звонке
- Персонализация: "здравствуйте, Мария Ивановна"
- Acceptance: повторный звонок → AI узнаёт клиента по номеру

### EPIC 6: Admin & Notifications (S17-S20)

#### S17: Admin Panel — Onboarding Wizard
- Пошаговый мастер подключения: SIP-номер, YClients API-ключ, приветствие, тон AI
- Без терминов из телефонии и AI
- Acceptance: владелец салона за 30 минут подключает всё самостоятельно

#### S18: Admin Panel — Dashboard
- История звонков с расшифровками
- Созданные записи
- Базовая статистика (принято звонков, записей, эскалаций)
- Acceptance: все разделы отображают данные тестового салона

#### S19: Telegram Bot for Owner
- Уведомления: новая запись, эскалация, системные алерты
- Команды: /status, /bookings, /settings
- Acceptance: владелец получает уведомление в Telegram после записи клиента

#### S20: SMS Reminders
- Напоминания за день и за час до визита
- Через Sipuni SMS API
- Acceptance: клиент получает SMS перед визитом

### EPIC 7: Testing & Documentation (S21-S24)

#### S21: Conversational Engine Tests
- Mock-диалоги по всем 5 сценариям
- Edge cases: акценты, шум, перебивания, нелогичные запросы
- Coverage ≥ 70%
- Acceptance: все тесты зелёные

#### S22: Booking Layer Tests
- Модульные тесты календаря и YClients адаптера
- Интеграционные тесты с YClients sandbox
- Coverage ≥ 80%
- Acceptance: все тесты зелёные

#### S23: E2E Tests
- Полный сценарий: звонок → ASR → диалог → запись в YClients
- Сценарий переноса
- Сценарий эскалации
- Acceptance: 3 E2E теста проходят на CI

#### S24: Documentation
- README.md с инструкцией развёртывания
- ARCHITECTURE.md
- ONBOARDING.md (как салон подключает Алло за 30 минут)
- API.md
- Acceptance: документация готова, посторонний разработчик поднимает проект по README
