FROM python:3.11-slim

WORKDIR /app

COPY apps/auth-service/pyproject.toml /app/pyproject.toml
COPY apps/auth-service/src /app/src
COPY infra/postgres /app/infra/postgres
COPY infra/render/scripts /app/infra/render/scripts

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir . \
  && chmod +x /app/infra/render/scripts/start-auth-service.sh

EXPOSE 9000

CMD ["uvicorn", "auth_service.main:app", "--host", "0.0.0.0", "--port", "9000"]
