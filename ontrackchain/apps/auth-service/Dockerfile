FROM python:3.11-slim

WORKDIR /app

ENV REBUILD_NONCE=20260808_v6_rls_middleware

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src
COPY tests /app/tests

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir ".[dev]"

EXPOSE 9000

CMD ["uvicorn", "auth_service.main:app", "--host", "0.0.0.0", "--port", "9000"]
