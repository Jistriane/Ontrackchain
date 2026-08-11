FROM python:3.11-slim

WORKDIR /app

ENV REBUILD_NONCE=20260811_v7_rbac_shared_first

COPY apps/mock-oidc/pyproject.toml /app/pyproject.toml
COPY apps/mock-oidc/src /app/src
COPY packages/shared /tmp/ontrackchain-shared

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir /tmp/ontrackchain-shared \
  && pip install --no-cache-dir .

EXPOSE 9101

CMD ["uvicorn", "mock_oidc.main:app", "--host", "0.0.0.0", "--port", "9101"]

