FROM python:3.11-slim

WORKDIR /app

COPY apps/report-api/pyproject.toml /app/pyproject.toml
COPY apps/report-api/src /app/src
COPY packages/shared /tmp/ontrackchain-shared
COPY packages/agents /tmp/ontrackchain-agents

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir /tmp/ontrackchain-shared \
  && pip install --no-cache-dir /tmp/ontrackchain-agents \
  && pip install --no-cache-dir .

EXPOSE 8004

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["uvicorn report_api.main:app --host 0.0.0.0 --port ${PORT:-8004}"]
