FROM python:3.12-slim

WORKDIR /app

# Copy gateway package
COPY gateway/pyproject.toml /app/
RUN pip install --no-cache-dir -e /app

# Copy source code
COPY gateway/ /app/

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
