FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies
COPY speech/pyproject.toml ./
RUN pip install --no-cache-dir fastapi>=0.115.0 uvicorn[standard]>=0.30.0 websockets>=12.0 pydantic>=2.0.0 httpx>=0.27.0

# Copy source code
COPY speech/ ./
COPY shared/ /app/shared/

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
