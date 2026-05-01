# Contributing to Алло

Thank you for your interest in contributing to Алло! This document covers the development workflow, coding standards, and how to get started.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Service Development](#service-development)
- [Testing](#testing)
- [Code Style](#code-style)
- [Git Workflow](#git-workflow)
- [Pull Request Process](#pull-request-process)
- [Environment Variables](#environment-variables)
- [Debugging Tips](#debugging-tips)

---

## Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose v2.22+
- Make
- uv (Python package manager) — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 1. Clone and set up

```bash
git clone git@github.com:vkrasnovid/allo.git
cd allo
make install       # Install all Python dependencies (uv sync per service)
make pre-commit    # Install pre-commit hooks
```

### 2. Start infrastructure services

```bash
docker compose up -d postgres redis minio
```

### 3. Start a specific service in dev mode

```bash
# For example, the Booking service
cd booking
uv run uvicorn src.main:app --reload --port 8003
```

### 4. Run migrations

```bash
make migrate   # Apply all Alembic migrations
make seed      # Load test data
```

---

## Project Structure

```
allo/
├── gateway/             # Layer 1: Voice Gateway (SIP + audio pipeline)
├── speech/              # Layer 2: ASR + TTS + VAD services
├── engine/              # Layer 3: Conversational Engine (LLM + dialog)
├── booking/             # Layer 4: Booking & CRM (calendar, YClients)
├── admin/               # Layer 5: Admin Panel (web UI for salon owners)
├── notifications/       # Layer 5: SMS & Telegram notifications
├── shared/              # Shared code: tools library, models, exceptions
│   ├── tools/           #   Tool interfaces and implementations
│   ├── models/          #   Shared Pydantic models
│   ├── exceptions/      #   Error hierarchy
│   └── utils/           #   Utilities (circuit breaker, logging, etc.)
├── openclaw-plugins/    # OpenClaw TypeScript plugins (booking, calendar, masters, tg-bot)
├── infra/               # Infrastructure configs (Caddy, PG, OpenClaw)
├── secrets/             # Docker secrets (gitignored)
└── .github/workflows/   # CI/CD
```

Each Python service follows the same internal structure:

```
service/
├── src/
│   ├── __init__.py
│   ├── main.py           # FastAPI app entrypoint
│   ├── api/              # REST / WebSocket handlers
│   ├── models/           # Domain models (SQLAlchemy + Pydantic)
│   └── services/         # Business logic
├── tests/                # Test suite
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## Development Workflow

### Service scope

| Service | What you can change | Port (dev) | Depends on |
|---------|-------------------|:----------:|------------|
| `gateway/` | SIP handling, audio pipeline, state machine | 8000 | Redis, postgres, speech, engine |
| `speech/` | ASR, TTS, VAD integrations | 8001 | Redis, Yandex SpeechKit |
| `engine/` | Dialog manager, prompts, tool executor | 8002 | Redis, postgres, booking, OpenClaw |
| `booking/` | Calendar, bookings, clients, YClients adapter | 8003 | postgres, redis |
| `admin/` | Web UI, stats, settings | 8004 | postgres, booking |
| `notifications/` | SMS, Telegram notifications | — | Redis, booking (via Celery) |
| `shared/` | Tool library, shared models, utils | — | None (pure Python) |

### Running a single service

```bash
# Start dependencies first
docker compose up -d postgres redis

# Run the service with hot reload
cd booking
uv run uvicorn src.main:app --reload --port 8003

# Run with full docker-compose override (mounts src as volume)
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d booking
```

### Adding a new dependency

```bash
cd booking
uv add httpx        # Production dependency
uv add pytest-mock --dev  # Dev dependency
```

---

## Testing

### Running tests per service

```bash
# Run all tests in a service
cd booking
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=term-missing

# Specific test file
uv run pytest tests/test_calendar.py -v

# Run tests matching a keyword
uv run pytest -k "yclients" -v
```

### Running all tests

```bash
make test     # Runs pytest on all services
make test-ci  # Same as CI — includes linting + type checking
```

### Writing tests

- **Place tests** in the `tests/` directory of each service, mirroring `src/` structure
- **Use pytest** as the test runner
- **Mock external services** (Yandex API, YClients, Sipuni, DeepSeek)
- **Use factories** for test data (factory_boy or simple fixtures)
- **Prefer async tests** for async services

**Example test:**

```python
# booking/tests/test_bookings.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_booking(client):
    response = await client.post(
        "/api/v1/tenants/test-uuid/bookings",
        json={
            "client_phone": "+79161234567",
            "client_name": "Мария",
            "master_id": "master-uuid",
            "service_id": "service-uuid",
            "start_at": "2026-05-15T14:00:00+03:00",
            "source": "phone",
        },
        headers={"X-Internal-API-Key": "test-key"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "confirmed"
    assert "booking_id" in data
```

### Mock dialogs (Engine tests)

The Engine has 100+ pre-defined test dialogs in `engine/tests/mock_dialogs/`:

```bash
cd engine
uv run pytest tests/test_mock_dialogs.py -v
```

These cover:
- Standard booking flow
- Repeat client (recognised by phone)
- "Just asking" scenario
- Reschedule / cancellation
- Escalation (complaint, aggression)
- Noise / heavy accent
- Barge-in (interruption)

### Anti-hallucination tests

```bash
cd engine
uv run pytest tests/anti_hallucination/ -v
```

These verify that the model never fabricates data (prices, names, times) — all values must come from tool outputs.

---

## Code Style

### Python

This project uses **ruff** for linting and formatting, and **mypy** for type checking.

```bash
# Check formatting and linting
cd booking
uv run ruff check src/
uv run ruff format src/ --check

# Auto-fix
uv run ruff check src/ --fix
uv run ruff format src/

# Type checking
uv run mypy src/
```

**Rules:**

| Tool | Config file | Key rules |
|------|-------------|-----------|
| **ruff** | `pyproject.toml` | Line length 100, `I` (isort), `UP` (pyupgrade), `B` (bugbear), `ANN` (annotations) |
| **mypy** | `pyproject.toml` | Strict mode, disallow `Any`, explicit `Optional` |

**Conventions:**

- **Type annotations** are mandatory for all function signatures
- **Async first** — all I/O-bound functions should be async
- **Pydantic v2** for all data schemas (request/response)
- **SQLAlchemy 2** ORM style (no legacy queries)
- **Dataclasses** for internal state objects
- **Protocol classes** for dependency injection interfaces

```python
# Good — typed, async, documented
from typing import Optional
from pydantic import BaseModel, Field
from datetime import date


class FindSlotsParams(BaseModel):
    """Parameters for finding available time slots."""
    master_id: Optional[str] = Field(None, description="Filter by master ID")
    service_id: Optional[str] = Field(None, description="Service ID for duration calculation")
    date: date = Field(..., description="Target date (YYYY-MM-DD)")


async def get_available_slots(
    tenant_id: str,
    params: FindSlotsParams,
    db: AsyncSession,
) -> list[dict]:
    """Query available slots for a given date and master."""
    ...
```

### TypeScript (OpenClaw plugins)

```bash
# Lint and format
cd openclaw-plugins/booking-plugin
npm run lint
npm run format
```

**Rules:**
- ESLint + Prettier
- TypeScript strict mode
- Async/await over promises

---

## Git Workflow

### Branch naming

```
feature/S16-client-database       # Features from stories
fix/booking-slot-overlap          # Bug fixes
docs/api-reference                # Documentation
refactor/engine-tool-executor     # Refactoring
test/anti-hallucination-suite     # Test additions
chore/update-deps                 # Maintenance
```

### Commit messages

Use conventional commits:

```
feat: add client database with phone-based identification
fix: prevent slot overlap in calendar booking
docs: add API reference for Booking Service
test: add 50 anti-hallucination test dialogs
refactor: extract tool executor into dedicated module
chore: update ruff to v0.5
```

### Feature branch workflow

```bash
# 1. Create a branch from main
git checkout main
git pull
git checkout -b feature/S16-client-database

# 2. Make changes, commit frequently
git add .
git commit -m "feat: add clients table and migration"
git commit -m "feat: implement client lookup by phone"
git commit -m "test: add client repository tests"

# 3. Keep branch up to date
git fetch origin
git rebase origin/main

# 4. Push and open a PR
git push -u origin feature/S16-client-database
```

### Rebasing vs merging

Prefer rebasing to keep a linear history:

```bash
git rebase origin/main
# Resolve conflicts if any, then:
git push --force-with-lease
```

---

## Pull Request Process

### Before opening a PR

1. **Run all tests** — `make test-ci`
2. **Check formatting** — `make lint`
3. **Type check** — `make typecheck`
4. **Update documentation** if the API changed
5. **Add or update tests** for new functionality

### PR template

```markdown
## Description

Implements client database (S16). Clients are identified by phone number
and stored with visit history and preferences.

## Story

S16: Client Database

## Changes

- Added `clients` table migration
- Implemented `ClientRepository` with async SQLAlchemy
- Added `GET /clients/by-phone/{phone}` endpoint
- Integrated client lookup in Engine (greeting by name)
- Added tests for repository and API

## Testing

- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual test: call from known number → greeted by name

## Screenshots

(if UI changes)

## Checklist

- [x] Code follows style guide (ruff + mypy happy)
- [x] Tests cover new code (coverage ≥ 80%)
- [x] API docs updated in API.md
- [x] No breaking changes to existing APIs
```

### Review expectations

- **At least 1 approval** required (maintainer or peer)
- **Max 400 lines** per PR (if larger, split into smaller PRs)
- **Respond to comments** within 48 hours
- **Squash merge** when approved (clean single commit per PR)

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

**Required for development (without these, some services won't start):**

| Variable | Service | How to get |
|----------|---------|------------|
| `YANDEX_SPEECHKIT_KEY` | speech | Yandex Cloud Console → SpeechKit |
| `SIPUNI_API_KEY` | gateway | Sipuni dashboard → API keys |
| `SIPUNI_ACCOUNT` | gateway | Sipuni account ID |
| `YCLIENTS_BEARER_TOKEN` | booking | YClients → Integration → API |
| `OPENCLAW_API_KEY` | engine, openclaw | Set any value for dev |
| `TELEGRAM_BOT_TOKEN` | notifications | @BotFather → create bot |

**For local development without SIP/telephony, you can leave the SIP-related variables empty** — the Gateway will start but won't accept calls.

### Docker secrets

Create the following files in `secrets/`:

```bash
secrets/
├── db_password.txt         # PostgreSQL password
├── minio_password.txt      # MinIO password
├── openclaw_api_key.txt    # OpenClaw API key
├── yandex_api_key.txt      # Yandex SpeechKit key
├── jwt_secret.txt          # JWT signing secret
└── encryption_key.txt      # Field encryption key
```

---

## Debugging Tips

### Logs

```bash
# Follow logs for a specific service
docker compose logs -f engine

# Last 100 lines with timestamps
docker compose logs --tail=100 -t booking

# Search logs for a specific call
docker compose logs engine | grep "call_id-uuid"
```

### Direct database access

```bash
docker compose exec postgres psql -U allo -d allo

# Example queries
SELECT * FROM tenants;
SELECT * FROM bookings WHERE tenant_id = 'uuid' ORDER BY start_at DESC;
SELECT * FROM calls WHERE status = 'failed';
```

### Redis (session state)

```bash
docker compose exec redis redis-cli -a $REDIS_PASSWORD

# List active sessions
KEYS "tenant-uuid:call-uuid:*"

# Get session data
GET "tenant-uuid:call-uuid:dialog_state"

# Monitor all commands (debugging)
MONITOR
```

### MinIO (audio files)

- Console: `http://localhost:9001` (credentials from `.env`)
- Bucket: `allo-audio`
- Path: `{tenant_id}/{date}/{call_id}.opus`

### Swagger UI

Each service exposes Swagger docs in development:

- Booking: `http://localhost:8003/docs`
- Admin: `http://localhost:8004/docs`
- Gateway: `http://localhost:8000/docs`

### Makefile commands

```bash
make help           # List all commands
make install        # Install dependencies for all services
make migrate        # Run Alembic migrations
make seed           # Load test data
make test           # Run all tests
make lint           # Run ruff on all services
make typecheck      # Run mypy on all services
make clean          # Reset local dev environment (docker down -v)
```

---

## Architecture Decisions

Key decisions are recorded in [ARCHITECTURE.md](./ARCHITECTURE.md) and `DECISIONS.md`:

1. **OpenClaw boundaries** — only text channels (Telegram, future WhatsApp). Voice engine is a dedicated Python service.
2. **Tool calling** — direct Python Tool Library for speed, OpenClaw TS plugins only as wrappers when orchestration is needed.
3. **Prompt system** — composable: base prompt + configurable blocks per tenant.
4. **Audio retention** — 90 days in S3, transcripts stored permanently. 152-ФЗ compliance built into pipeline.

See `DECISIONS.md` for the full history.
