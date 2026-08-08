FROM python:3.11-slim

WORKDIR /app

ENV REBUILD_NONCE=20260808_cm_rls_v6

COPY apps/case-management/pyproject.toml /app/pyproject.toml
COPY apps/case-management/src /app/src
COPY apps/case-management/tests /app/tests

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir ".[dev]"

EXPOSE 8006

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["uvicorn case_management.main:app --host 0.0.0.0 --port ${PORT:-8006}"]
