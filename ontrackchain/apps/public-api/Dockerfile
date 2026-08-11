FROM python:3.11-slim

WORKDIR /app

ENV REBUILD_NONCE=20260811_v7_rbac_shared_first

COPY apps/public-api/pyproject.toml /app/pyproject.toml
COPY apps/public-api/src /app/src
COPY packages/shared /tmp/ontrackchain-shared

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir /tmp/ontrackchain-shared \
  && pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "public_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
