FROM python:3.11-slim

WORKDIR /app

ENV REBUILD_NONCE=20260720_v3

COPY apps/investigation-api/pyproject.toml /app/pyproject.toml
COPY apps/investigation-api/src /app/src
COPY packages/agents /tmp/ontrackchain-agents

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir /tmp/ontrackchain-agents \
  && pip install --no-cache-dir .

EXPOSE 8001

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["uvicorn investigation_api.main:app --host 0.0.0.0 --port ${PORT:-8001}"]
