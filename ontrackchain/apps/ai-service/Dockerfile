FROM python:3.11-slim

WORKDIR /app

ENV REBUILD_NONCE=20260726_v2

COPY packages/shared /tmp/ontrackchain-shared
COPY packages/agents /tmp/ontrackchain-agents
COPY apps/ai-service/pyproject.toml /app/pyproject.toml
COPY apps/ai-service/src /app/src

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir /tmp/ontrackchain-shared \
  && pip install --no-cache-dir "/tmp/ontrackchain-agents[all]" \
  && pip install --no-cache-dir ".[llm]"

EXPOSE 8005

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["uvicorn ai_service.main:app --host 0.0.0.0 --port ${PORT:-8005}"]
