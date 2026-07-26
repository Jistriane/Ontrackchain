FROM python:3.11-slim

WORKDIR /app

ENV REBUILD_NONCE=20260726_v1

COPY apps/case-management/pyproject.toml /app/pyproject.toml
COPY apps/case-management/src /app/src

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir .

EXPOSE 8006

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["uvicorn case_management.main:app --host 0.0.0.0 --port ${PORT:-8006}"]
