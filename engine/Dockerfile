FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY engine/pyproject.toml ./
RUN pip install --no-cache-dir fastapi>=0.110 uvicorn[standard]>=0.27 pydantic>=2.6 pydantic-settings>=2.1 redis>=5.0 httpx>=0.27 sse-starlette>=2.0

# Copy source code
COPY engine/ ./
COPY shared/ /app/shared/

ENV PYTHONPATH=/app

EXPOSE 8002

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
