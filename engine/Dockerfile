FROM python:3.11-slim

WORKDIR /app

# Copy engine package
COPY engine/pyproject.toml /app/
RUN pip install --no-cache-dir -e /app

# Copy source code and shared library
COPY engine/src/ /app/src/
COPY shared/ /app/shared/
ENV PYTHONPATH=/app

EXPOSE 8002

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
