FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .[dev]

COPY src/ src/

RUN mkdir -p /app/shared && ln -sf /opt/allo/shared /app/shared 2>/dev/null || true

EXPOSE 8002

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
