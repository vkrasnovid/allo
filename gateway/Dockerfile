FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY gateway/pyproject.toml ./
RUN pip install --no-cache-dir fastapi>=0.115.0 uvicorn[standard]>=0.30.0 sqlalchemy[asyncio]>=2.0.30 asyncpg>=0.30.0 pydantic>=2.0.0 websockets>=12.0 httpx>=0.27.0

# Copy source code
COPY gateway/ ./

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
