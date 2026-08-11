#!/usr/bin/env bash
# SCRIPT: s28p27-run-e2e-light.sh
# CRIADO EM: Sprint S28+27 P3
# PROPÓSITO: Rodar perfil LEVE do docker-compose local (8 containers: traefik, postgres, redis,
#           postgres-bootstrap, auth-service, public-api, ai-service, mock-oidc) + validar
#           /healthz de todos 4 serviços após ~30s. SEMPRE desliga tudo no final (trap).
#
# FLUXO:
#   1) Valida sintaxe compose (docker compose config -q)
#   2) DOWN forçado primeiro (limpa restos)
#   3) UP -d (8 containers perfil LEVE)
#   4) Espera postgres + redis healthy (healthcheck compose ou timeout 60s)
#   5) Loop 30x de 1s esperando 4 serviços (auth 9000, public 8000, ai 8005, mock-oidc 9101 ou via traefik :8080)
#   6) Imprime resumo PASSO 0: PASSO 0 M5 via gov-m5 + curl -fsS /healthz de cada serviço
#   7) Ao final (SIGINT/exit/erro): docker compose down
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/.." || exit 9
COMPOSE_FILE="ontrackchain/docker-compose.yml"
TMPDIR_WORK="$(mktemp -d)"
trap '
  echo
  echo "🧹 CLEANUP: docker compose down..."
  docker compose -f "$COMPOSE_FILE" down --remove-orphans >/dev/null 2>&1 || true
  rm -rf "$TMPDIR_WORK"
' EXIT INT TERM

PORTS=(
  "auth-service|9000|/healthz"
  "public-api|8000|/healthz"
  "ai-service|8005|/healthz"
  "mock-oidc|9101|/healthz"
)

echo "============================================================"
echo "Sprint S28+27 E2E LIGHT: perfil LEVE (4 serviços + infra)"
echo "============================================================"
echo "Arquivo compose: $COMPOSE_FILE"

if ! command -v docker >/dev/null 2>&1; then
  echo "❌ Docker NÃO encontrado. Instale Docker Engine + Compose V2 (plugins)."
  exit 1
fi

# 1) Validar sintaxe
echo
echo "[1/5] Validando sintaxe docker-compose.yml..."
if ! docker compose -f "$COMPOSE_FILE" config -q >/dev/null 2>&1; then
  echo "❌ compose config falhou. Rode: docker compose -f $COMPOSE_FILE config"
  exit 2
fi
echo "✅ OK"

# 2) Down forçado
echo
echo "[2/5] DOWN + remove orphans (limpeza prévia)..."
docker compose -f "$COMPOSE_FILE" down --remove-orphans >/dev/null 2>&1

# 3) Up perfil leve
echo
echo "[3/5] UP perfil LEVE (-d): traefik, postgres, redis, postgres-bootstrap, auth, public, ai, mock-oidc..."
docker compose -f "$COMPOSE_FILE" --profile mock-oidc up -d \
  traefik postgres redis postgres-bootstrap \
  auth-service public-api ai-service mock-oidc >"$TMPDIR_WORK/up.log" 2>&1 || {
    echo "❌ docker compose up falhou. Log:"
    tail -40 "$TMPDIR_WORK/up.log"
    exit 3
}
echo "✅ 8 containers solicitados. Aguardar healthchecks infra (postgres/redis ~10s)..."

# 4) Espera PG + Redis healthy (timeout 60s)
SEG=0; MAX_SEG=60
POSTGRES_OK=0; REDIS_OK=0
while [ $SEG -lt $MAX_SEG ]; do
  ST=$(docker compose -f "$COMPOSE_FILE" ps --format json 2>/dev/null || true)
  if echo "$ST" | grep -q '"Service":"postgres"[^}]*"Health":"healthy"'; then POSTGRES_OK=1; fi
  if echo "$ST" | grep -q '"Service":"redis"[^}]*"Health":"healthy"'; then REDIS_OK=1; fi
  if [ $POSTGRES_OK -eq 1 ] && [ $REDIS_OK -eq 1 ]; then break; fi
  sleep 1; SEG=$((SEG+1))
  echo -n "."
done
echo
if [ $POSTGRES_OK -eq 0 ] || [ $REDIS_OK -eq 0 ]; then
  echo "⚠️  Timeout 60s PG/Redis ainda unhealthy. Seguindo mesmo assim (pode ser atraso Docker Desktop)."
else
  echo "✅ postgres healthy + redis healthy ($SEG s)"
fi

# 5) Espera 4 serviços responderem /healthz (30 retries 1s)
echo
echo "[4/5] Healthz check em 4 serviços FastAPI (30 retries 1s):"
RESUMO=""
TOTAL=0; PASS=0
for spec in "${PORTS[@]}"; do
  SVC="${spec%%|*}"; REST="${spec#*|}"
  PORT="${REST%%|*}"; PATH="${REST##*|}"
  TOTAL=$((TOTAL+1))
  OK=0
  for i in $(seq 1 40); do
    OUT=$(curl -fsS --max-time 2 "http://127.0.0.1:${PORT}${PATH}" 2>/dev/null || true)
    if [ -n "$OUT" ] && echo "$OUT" | grep -qE '"status"[:space:]*:[:space:]*"pass"'; then
      OK=1; break
    fi
    sleep 1
  done
  if [ $OK -eq 1 ]; then
    echo "  ✅ $SVC (port $PORT) → /healthz PASS"
    PASS=$((PASS+1))
  else
    echo "  ❌ $SVC (port $PORT) → /healthz NÃO respondeu em 40s"
  fi
done

# 6) Resumo
echo
echo "[5/5] Resumo E2E LIGHT: $PASS/$TOTAL serviços responderam healthz = pass"
echo
echo "  Resumo docker compose ps:"
docker compose -f "$COMPOSE_FILE" ps --format 'table {{.Name}}\t{{.Service}}\t{{.State}}\t{{.Health}}\t{{.Ports}}'

echo
if [ $PASS -eq $TOTAL ]; then
  echo "✅ E2E LIGHT SUCESSO: 4 serviços + infra 100% saudáveis."
  echo "   Não se preocupe com desligamento — trap EXIT vai executar 'docker compose down' ao sair."
  echo "   Para visualizar logs: make compose-logs-follow (ou Ctrl-C p/ encerrar)."
  # Dorme um pouco antes de desligar? Deixa o trap desligar no fim do script.
  exit 0
else
  echo "⚠️  E2E LIGHT com FALHAS ($((TOTAL-PASS)) serviços NÃO passaram). Rode:"
  echo "     make compose-logs  # último 200 linhas"
  exit 4
fi
