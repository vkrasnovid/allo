FROM python:3.12-slim

WORKDIR /app

# Copy speech package
COPY speech/pyproject.toml /app/
RUN pip install --no-cache-dir -e /app

# Copy source code
COPY speech/ /app/

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
