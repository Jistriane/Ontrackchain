FROM python:3.11-slim

WORKDIR /app

COPY apps/ai-service/pyproject.toml /app/pyproject.toml
COPY apps/ai-service/src /app/src

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir .

EXPOSE 8005

CMD ["uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8005"]
