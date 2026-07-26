FROM python:3.11-slim

WORKDIR /app

COPY packages/agents /app/packages/agents
COPY apps/ai-service/src /app/src

ENV PYTHONPATH=/app/src:/app/packages/agents/src

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings "psycopg[binary]>=3.2.0" "psycopg_pool>=3.2.0" \
  && pip install --no-cache-dir anthropic groq voyageai \
  && pip install --no-cache-dir /app/packages/agents

EXPOSE 8005

CMD ["uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8005"]
