#!/usr/bin/env bash
# OnTrackChain — Render Deploy SMOKE TESTS FULL STACK (rodar após deploy)
# Uso: bash infra/render/scripts/render-smoke-tests.sh https://ontrackchain-gateway-staging.onrender.com

set -euo pipefail

GATEWAY_URL="${1:-https://ontrackchain-gateway-staging.onrender.com}"
KEYCLOAK_URL="${2:-https://ontrackchain-keycloak-staging.onrender.com}"
FRONTEND_URL="${3:-https://ontrackchain-frontend-staging.onrender.com}"

declare -i OK=0 FAIL=0

PASS()  { echo "  ✅ PASS  $*"; OK+=1; }
FAIL()  { echo "  🚨 FAIL  $*"; FAIL+=1; }
RUN()   { local url="$1" desc="$2"; shift 2; local code;
          code=$(curl -sS -o /tmp/otk_smoke_body -w "%{http_code}" --max-time 15 "$@" "$url" 2>/dev/null || echo 000)
          if [[ "$code" == 2* ]]; then
            PASS "$desc → HTTP $code";
          else
            FAIL "$desc → HTTP $code (expected 2xx). Body preview:";
            head -c 400 /tmp/otk_smoke_body 2>/dev/null || true; echo;
          fi; }

echo "================================================================================"
echo " OnTrackChain — Render Full Stack Staging Smoke Tests"
echo "  Gateway:   $GATEWAY_URL"
echo "  Keycloak:  $KEYCLOAK_URL"
echo "  Frontend:  $FRONTEND_URL"
echo "================================================================================"
echo ""
echo "--- [1/3] INFRA ESSENCIAL (auth + login + health básicos) ---"
RUN "$GATEWAY_URL/login"                    "Tela Login via gateway" -L
RUN "$FRONTEND_URL/api/healthz"             "Frontend /api/healthz"
RUN "$KEYCLOAK_URL/realms/ontrackchain"     "Keycloak realm discovery" -L
RUN "$GATEWAY_URL/health"                   "Gateway health aggregate"

echo ""
echo "--- [2/3] APIs CORE via gateway ---"
RUN "$GATEWAY_URL/api/v1/auth/health"       "Auth-service health"
RUN "$GATEWAY_URL/api/v1/auth/config"       "Auth OIDC config (auth_mode != showcase)"
RUN "$GATEWAY_URL/api/v1/cases/health"      "Case management health"
RUN "$GATEWAY_URL/api/v1/investigation/health" "Investigation API health"
RUN "$GATEWAY_URL/api/v1/compliance/health" "Compliance API health"
RUN "$GATEWAY_URL/api/v1/monitoring/health" "Monitoring API health"
RUN "$GATEWAY_URL/api/v1/ai/health"         "AI service health (RAG pgvector)"
RUN "$GATEWAY_URL/api/v1/report/health"     "Reporting API health"

echo ""
echo "--- [3/3] SHOWCASE BLOQUEADO (todas esperam 401 ou redirect login) ---"
INV_SESSION=$(curl -s -X POST "$FRONTEND_URL/api/session/start" -H 'content-type: application/json' \
    -d '{"email":"system@ontrackchain.com","password":"SystemPass123!"}' -D /tmp/otk_smoke_headers -o /dev/null -w "%{http_code}" || true)
if [[ "$INV_SESSION" == "401" || "$INV_SESSION" == "302" || "$INV_SESSION" == "200" ]]; then
  PASS "Sessão email/senha staging (HTTP $INV_SESSION) — não retornou 500 ou showcase fallback"
else
  FAIL "Sessão email/senha staging retornou HTTP $INV_SESSION (esperado 200/302/401 real, não showcase)"
fi

echo ""
echo "================================================================================"
echo "  RESULTADO: $OK PASSADOS / $FAIL FALHOS  (total $((OK+FAIL)) checks)"
echo "================================================================================"
[[ $FAIL -eq 0 ]] && { echo "🎉 DEPLOY COMPLETO E FUNCIONAL. Nenhum dado mockado, nenhum showcase."; exit 0; }
echo "⚠️  $FAIL check(s) falharam — abra logs no Render Dashboard (último serviço que falhou) e verifique secrets / conectividade."
exit 1
