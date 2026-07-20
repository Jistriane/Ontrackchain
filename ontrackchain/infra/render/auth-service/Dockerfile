FROM python:3.11-slim

WORKDIR /app

COPY apps/auth-service/pyproject.toml /app/pyproject.toml
COPY apps/auth-service/src /app/src
COPY infra/postgres /app/infra/postgres
COPY infra/render/scripts /app/infra/render/scripts
COPY infra/postgres /infra/postgres
COPY infra/render/scripts /infra/render/scripts

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir hatchling \
  && pip install --no-cache-dir . \
  && chmod +x /app/infra/render/scripts/start-auth-service.sh \
  && chmod +x /infra/render/scripts/start-auth-service.sh \
  && ln -sf /usr/local/bin/python3 /usr/bin/python3 \
  && ln -sf /usr/local/bin/python3 /bin/python3 \
  && ln -sf /usr/local/bin/uvicorn /usr/bin/uvicorn \
  && ln -sf /usr/local/bin/uvicorn /bin/uvicorn

EXPOSE 9000

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["/app/infra/render/scripts/start-auth-service.sh"]
