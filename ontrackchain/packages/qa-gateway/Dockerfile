# imagem standalone do QA Gateway CLI (exige apenas packages/qa-gateway).
# Build exemplo:
#   docker build -t otk-qa-gateway -f packages/qa-gateway/Dockerfile .
# Uso exemplo:
#   docker run --rm -e ONTRACKCHAIN_DATABASE_URL=postgresql://u:p@host:5432/ontrack \
#       otk-qa-gateway qa-gateway scan-rls
#   docker run --rm otk-qa-gateway qa-gateway health \
#       --endpoints "https://staging.ontrackchain.com/api/v1/auth/healthz,https://staging.ontrackchain.com/api/v1/cases/healthz"
FROM python:3.11-slim

WORKDIR /app

ENV REBUILD_NONCE=20260808_qagw_cli_v2_optimized \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 1. Deps do host + user não-root
RUN apt-get update -y \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && addgroup --system --gid 10001 appuser \
 && adduser --system --uid 10001 --ingroup appuser --no-create-home --shell /usr/sbin/nologin appuser \
 && apt-get clean -y && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir --upgrade pip hatchling wheel

# 2. Package QA Gateway (fonte única da verdade)
COPY --chown=appuser:appuser packages/qa-gateway /tmp/ontrackchain-qa-gateway
RUN pip install --no-cache-dir /tmp/ontrackchain-qa-gateway \
 && rm -rf /tmp/ontrackchain-qa-gateway

# 3. Smoke test: os 3 comandos existem (--help não falha)
RUN qa-gateway --version \
 && qa-gateway scan-rls --help >/dev/null \
 && qa-gateway health --help >/dev/null \
 && qa-gateway scan-lgpd --help >/dev/null \
 && echo "SMOKE OK (CLI 3 comandos disponíveis)"

USER appuser

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["qa-gateway --help"]
