# Алло — Deployment Guide

> Голосовой AI-секретарь для сферы услуг

## Quick Start

```bash
# 1. Clone and setup
git clone git@github.com:vkrasnovid/allo.git
cd allo
cp .env.example .env
# Edit .env with your secrets

# 2. Start all services
docker compose up -d

# 3. Run migrations (auto on booking start)
docker compose logs booking
```

## Services

| Service | Internal Port | Layer | Description | Health Check |
|---------|---------------|-------|-------------|-------------|
| **postgres** | 5432 | Infra | PostgreSQL 15 database | Built-in (pg_isready) |
| **redis** | 6379 | Infra | Session state & queues | Built-in (redis-cli ping) |
| **minio** | 9000 | Infra | S3-compatible audio storage | Built-in (HTTP health) |
| **booking** | 8003 | Layer 4 | Booking & CRM API | `/api/v1/health` |
| **engine** | 8002 | Layer 3 | Conversational Engine (LLM) | `/health` |
| **gateway** | 8000 | Layer 1 | Voice Gateway (SIP) | `/health` |
| **speech** | 8001 | Layer 2 | Yandex SpeechKit ASR/TTS/VAD | `/health` |
| **admin** | 3000 | Layer 5 | Next.js 14 admin panel | `/` (200) |
| **notifications** | 8005 | Layer 5 | Telegram & SMS notifications | `/health` |

## Health Checks

All services expose health endpoints on their configured ports:

```bash
# Check all services (run from a container on the same network)
docker compose run --rm --no-deps --entrypoint sh gateway \
  -c 'apk add curl && for svc in gateway:8000 engine:8002 speech:8001 notifications:8005 booking:8003; do \
    echo "=== $svc ===" && curl -sf "http://$svc/health" 2>/dev/null || \
    curl -sf "http://$svc/api/v1/health" 2>/dev/null; done'

# Individual checks (via docker compose internal network)
docker compose exec gateway python -c "
import urllib.request, json
for svc in [('engine','http://engine:8002'),('speech','http://speech:8001'),('notifications','http://notifications:8005')]:
    r=urllib.request.urlopen(svc[1]+'/health',timeout=5)
    print(json.dumps(json.loads(r.read().decode()),indent=2))
"
```

## Building

```bash
# Build all services
docker compose build

# Build specific service
docker compose build booking

# Build and start specific service
docker compose up -d --build booking
```

## Database Migrations

Migrations run automatically on booking service startup. To run them manually:

```bash
docker compose exec booking alembic upgrade head
docker compose exec booking python seed.py  # seed test data
```

## CI/CD

### CI (`.github/workflows/ci.yml`)
Triggers on push to `main`/`develop` and PRs to `main`:
- **Ruff lint** — Python code style checks
- **Pytest** — Unit tests with Postgres + Redis service containers
- **Docker build** — Verify all images build successfully

### Deploy (`.github/workflows/deploy.yml`)
Triggers on push to `main` or manual dispatch:
- Builds Docker images
- Deploys to VPS via SSH
- Creates `.env` from GitHub Secrets
- Runs `docker compose up -d`
- Verifies health endpoints
- Notifies via Telegram

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `SSH_HOST` | VPS IP address |
| `SSH_USER` | SSH username |
| `SSH_KEY` | SSH private key |
| `DB_PASSWORD` | PostgreSQL password |
| `REDIS_PASSWORD` | Redis password |
| `MINIO_ROOT_USER` | MinIO access key |
| `MINIO_PASSWORD` | MinIO secret key |
| `YANDEX_SPEECHKIT_KEY` | Yandex SpeechKit API key |
| `OPENCLAW_API_KEY` | OpenClaw API key |
| `SIPUNI_API_KEY` | Sipuni API key |
| `SIPUNI_ACCOUNT` | Sipuni account |
| `SIPUNI_SECRET` | Sipuni secret |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat for notifications |
| `JWT_SECRET` | JWT signing secret |
| `ENCRYPTION_KEY` | Data encryption key |

## Environment Variables

See `.env.example` for all required variables:

```ini
DB_PASSWORD=            # PostgreSQL password
REDIS_PASSWORD=         # Redis password
MINIO_ROOT_USER=allo_admin
MINIO_PASSWORD=         # MinIO secret key
YANDEX_SPEECHKIT_KEY=   # Yandex SpeechKit API key
OPENCLAW_API_KEY=       # OpenClaw endpoint API key
SIPUNI_API_KEY=         # Sipuni SIP API key
SIPUNI_ACCOUNT=         # Sipuni account
SIPUNI_SECRET=          # Sipuni webhook secret
TELEGRAM_BOT_TOKEN=     # Telegram bot token
JWT_SECRET=             # JWT signing secret (change in production)
ENCRYPTION_KEY=         # Data encryption key (change in production)
```

## Production Deployment

```bash
# On VPS:
git clone git@github.com:vkrasnovid/allo.git /opt/allo
cd /opt/allo
cp .env.example .env

# Edit .env with production secrets (nano .env)
# Set strong passwords, valid API keys, etc.

# Start infrastructure first
docker compose up -d postgres redis minio

# Wait for database to be healthy
docker compose logs postgres

# Start remaining services
docker compose up -d

# Verify all health endpoints
docker compose exec booking python -c "import urllib.request; r=urllib.request.urlopen('http://engine:8002/health',timeout=5); print('Engine:',r.status)"
```

## Architecture

```
 Layer 1: Gateway (port 8000) — SIP integration, call management
 Layer 2: Speech (port 8001)  — ASR/TTS/VAD via Yandex SpeechKit
 Layer 3: Engine (port 8002)  — Conversational AI, dialog management
 Layer 4: Booking (port 8003) — CRM, scheduling, database
 Layer 5: Admin (port 3000)   — Next.js admin panel
 Layer 5: Notifications (port 8005) — Telegram & SMS
```

## Troubleshooting

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f gateway

# Restart a service
docker compose restart engine

# Rebuild and restart
docker compose up -d --build booking

# Reset everything
docker compose down -v   # WARNING: removes volumes
docker compose up -d
```

## GitHub

- **Repository**: https://github.com/vkrasnovid/allo
- **License**: Proprietary
