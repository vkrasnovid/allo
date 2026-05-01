FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY notifications/pyproject.toml ./
RUN pip install --no-cache-dir fastapi>=0.110 uvicorn[standard]>=0.27 pydantic>=2.6 pydantic-settings>=2.1 celery>=5.3 redis>=5.0 httpx>=0.27

# Copy source code
COPY notifications/ ./
COPY shared/ /app/shared/

ENV PYTHONPATH=/app

EXPOSE 8005

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005"]
