FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY booking/pyproject.toml ./
RUN pip install --no-cache-dir fastapi>=0.110 uvicorn[standard]>=0.27 sqlalchemy[asyncio]>=2.0 asyncpg>=0.29 alembic>=1.13 pydantic>=2.6 pydantic-settings>=2.1 redis>=5.0 celery>=5.3 httpx>=0.27 minio>=7.2

# Copy source code
COPY booking/ ./
COPY shared/ /app/shared/

ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
