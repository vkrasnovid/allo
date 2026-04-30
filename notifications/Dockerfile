FROM python:3.11-slim

WORKDIR /app

# Copy notifications package
COPY notifications/pyproject.toml /app/
RUN pip install --no-cache-dir -e /app

# Copy source code
COPY notifications/ /app/

ENV PYTHONPATH=/app
EXPOSE 8005

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8005"]
