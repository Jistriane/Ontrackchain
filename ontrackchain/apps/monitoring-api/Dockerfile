FROM python:3.11-slim

WORKDIR /app

COPY apps/monitoring-api/pyproject.toml /app/pyproject.toml
COPY apps/monitoring-api/src /app/src
COPY packages/shared /tmp/ontrackchain-shared

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir /tmp/ontrackchain-shared \
  && pip install --no-cache-dir .

EXPOSE 8003

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["uvicorn monitoring_api.main:app --host 0.0.0.0 --port ${PORT:-8003}"]
