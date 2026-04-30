FROM python:3.12-slim

WORKDIR /app

# Copy booking package
COPY booking/pyproject.toml /app/
RUN pip install --no-cache-dir -e /app

# Copy source code and shared library
COPY booking/ /app/
COPY shared/ /app/shared/
ENV PYTHONPATH=/app
EXPOSE 8003

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
