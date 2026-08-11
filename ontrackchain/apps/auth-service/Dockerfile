FROM python:3.11-slim

WORKDIR /app

ENV REBUILD_NONCE=20260811_v7_rbac_shared_first

COPY apps/auth-service/pyproject.toml /app/pyproject.toml
COPY apps/auth-service/src /app/src
COPY apps/auth-service/tests /app/tests
COPY packages/shared /tmp/ontrackchain-shared

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir /tmp/ontrackchain-shared \
  && pip install --no-cache-dir ".[dev]"

EXPOSE 9000

CMD ["uvicorn", "auth_service.main:app", "--host", "0.0.0.0", "--port", "9000"]
