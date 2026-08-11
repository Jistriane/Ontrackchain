FROM python:3.11-slim

# Sprint S28+50 P4: single-stage otimizado (non-root + PYTHONUNBUFFERED + HEALTHCHECK + layer cache)
# Serviço: mock-oidc

WORKDIR /app

ENV REBUILD_NONCE=20260811_v8_rbac_shared_first_optimized \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 1. Criar user não-root (UID/GID estáveis 10001) + ca-certificates para HTTPS (urllib healthcheck)
RUN apt-get update -y \
 && apt-get install -y --no-install-recommends ca-certificates \
 && addgroup --system --gid 10001 appuser \
 && adduser --system --uid 10001 --ingroup appuser --no-create-home --shell /usr/sbin/nologin appuser \
 && apt-get clean -y && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir --upgrade pip hatchling wheel

# 2. Camada deps (menos mutável — shared → agents → pyproject para max cache hit)
COPY packages/shared /tmp/ontrackchain-shared
COPY apps/mock-oidc/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir /tmp/ontrackchain-shared \
  && pip install --no-cache-dir . \
  && rm -rf /tmp/ontrackchain-*

# 3. Camada fonte (mais mutável — invalida apenas COPY abaixo)
COPY --chown=appuser:appuser apps/mock-oidc/src /app/src

EXPOSE 9101

# 4. Healthcheck via urllib stdlib (zero deps novas) apontando para /healthz
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request,sys; r=urllib.request.urlopen('http://localhost:${PORT:-9101}/healthz', timeout=2); sys.exit(0 if r.status==200 else 1)" || exit 1

# 5. Executar como usuário não-root
USER appuser

# 6. CMD usa 'exec' (sh PID 1 → python PID 1) para receber SIGTERM corretamente
CMD ["sh", "-c", "exec uvicorn mock_oidc.main:app --host 0.0.0.0 --port ${PORT:-9101}"]
