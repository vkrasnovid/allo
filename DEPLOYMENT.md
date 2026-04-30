# Алло — Deployment Guide

> Голосовой AI-секретарь для сферы услуг

## Quick Start

```bash
# 1. Clone and setup
git clone git@github.com:vkrasnovid/allo.git
cd allo
cp .env.example .env
# Edit .env with your secrets

# 2. Start infrastructure
docker compose up -d postgres redis minio

# 3. Run migrations (auto on booking start)
docker compose up -d booking

# 4. Start all services
docker compose up -d
```

## Services

| Service | Port | Layer | Description |
|---------|------|-------|-------------|
| **postgres** | 5432 | Infra | PostgreSQL 15 database |
| **redis** | 6379 | Infra | Session state & queues |
| **minio** | 9000 | Infra | S3-compatible audio storage |
| **booking** | 8003 | Layer 4 | Booking & CRM API |
| **engine** | 8002 | Layer 3 | Conversational Engine (LLM) |
| **gateway** | 8000 | Layer 1 | Voice Gateway (SIP) |
| **speech** | 8001 | Layer 2 | ASR/TTS/VAD services |
| **admin** | 3000 | Layer 5 | Next.js admin panel |
| **notifications** | 8005 | Layer 5 | Telegram & SMS notifications |

## Health Checks

```bash
# Engine
curl http://localhost:8002/health

# Booking API (valid UUID required)
curl http://localhost:8003/api/v1/tenants/<uuid>/info
```

## Building

```bash
# Build all services
docker compose build

# Build specific service
docker compose build booking
```

## CI/CD

- **CI**: GitHub Actions (`.github/workflows/ci.yml`)
  - Ruff lint
  - Pytest with Postgres + Redis services
  - Docker build

## Environment Variables

See `.env.example` for all required variables:

| Variable | Description |
|----------|-------------|
| `DB_PASSWORD` | PostgreSQL password |
| `REDIS_PASSWORD` | Redis password |
| `MINIO_ROOT_USER` | MinIO access key |
| `MINIO_PASSWORD` | MinIO secret key |
| `YANDEX_SPEECHKIT_KEY` | Yandex SpeechKit API key |
| `OPENCLAW_API_KEY` | OpenClaw API key |
| `SIPUNI_API_KEY` | Sipuni SIP API key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |

## GitHub

- **Repository**: https://github.com/vkrasnovid/allo
- **License**: Proprietary
