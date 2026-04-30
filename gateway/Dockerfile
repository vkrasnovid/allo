FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "gateway.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
