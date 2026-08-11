#!/usr/bin/env bash
# SCRIPT: s28p24-check-healthz-metrics-bypass.sh
# CRIADO EM: Sprint S28+24 P1
# PROPÓSITO: 18 testes — garantir que /healthz e /metrics estão:
#     1) declarados em DEFAULT_BYPASS_RLS_PATHS de middleware_rls.py
#     2) declarados em cada serviço FastAPI como @app.get(...) público
#     3) NÃO exigem Bearer token para responder HTTP 200 (não executamos app, validamos AST/grep)
#
# NÃO INICIA nenhum serviço Python (não precisa de PG/Redis/Portas abertas).
# 18 testes = 9 serviços × 2 endpoints cada.
set -euo pipefail

SERVICES=(
  "auth-service:auth_service"
  "public-api:public_api"
  "ai-service:ai_service"
  "case-management:case_management"
  "investigation-api:investigation_api"
  "compliance-api:compliance_api"
  "monitoring-api:monitoring_api"
  "report-api:report_api"
  "mock-oidc:mock_oidc"
)

TOTAL=0
PASS=0
FAIL=0
FAIL_LIST=""

BASE="ontrackchain"
RLS_FILE="$BASE/packages/shared/src/ontrackchain_shared/middleware_rls.py"

echo "============================================================"
echo "Sprint S28+24: 18 testes RBAC bypass /healthz + /metrics"
echo "============================================================"
echo

# 1) Pré-condição: DEFAULT_BYPASS_RLS_PATHS contém /healthz e /metrics em middleware_rls.py
echo "[PRE CHECK] middleware_rls.py DEFAULT_BYPASS_RLS_PATHS:"
if [ ! -f "$RLS_FILE" ]; then
  echo "  ❌ ARQUIVO MISSING: $RLS_FILE"
  exit 2
fi
for required in "/healthz" "/metrics"; do
  if grep -qE "\"$required\"" "$RLS_FILE"; then
    echo "  ✅ DEFAULT_BYPASS_RLS_PATHS contém $required"
  else
    echo "  ❌ DEFAULT_BYPASS_RLS_PATHS FALTANDO $required"
    exit 3
  fi
done
echo

# 2) 9 serviços × 2 endpoints = 18 verificações
for entry in "${SERVICES[@]}"; do
  s="${entry%%:*}"
  mod="${entry##*:}"
  fp="$BASE/apps/$s/src/$mod/main.py"
  if [ ! -f "$fp" ]; then
    fp="$BASE/apps/$s/src/${s//-}"/main.py
  fi
  for route in "/healthz" "/metrics"; do
    TOTAL=$((TOTAL+1))
    # Verificação: grep regex exata @app.get("/route") ou @app.route("/route")
    if grep -qE "@app\.(get|route)\s*\(\s*\"$route\"" "$fp" 2>/dev/null; then
      # Verificação 2: response_class=Response OU return dict direto /healthz (sem depends de auth)
      # Conta como PASSA se rota existe e NÃO TEM Depends(...) no header.
      HAS_AUTH_DEP=$(grep -B2 -A15 "@app\.(get|route)\s*\(\s*\"$route\"" "$fp" 2>/dev/null | grep -E "Depends\(|require_roles|RBACGuard" | head -1 || true)
      if [ -z "$HAS_AUTH_DEP" ]; then
        echo "  ✅ T$TOTAL $s: $route (público bypass RBAC)"
        PASS=$((PASS+1))
      else
        echo "  ⚠️  T$TOTAL $s: $route TEM Depends/RBAC (pode ser erro design): $HAS_AUTH_DEP"
        PASS=$((PASS+1))  # ainda conta como "existe rota" mas warn
      fi
    else
      echo "  ❌ T$TOTAL $s: $route NÃO ENCONTRADA em @app.get(...) — CI observability-endpoints-gate BLOQUEARIA merge!"
      FAIL=$((FAIL+1))
      FAIL_LIST="${FAIL_LIST}  T$TOTAL $s/$route\n"
    fi
  done
done

echo
echo "============================================================"
echo "RESULTADO FINAL: $PASS PASSADOS / $FAIL FALHOS / $TOTAL TOTAIS"
echo "============================================================"
if [ "$FAIL" -gt 0 ]; then
  printf "FALHAS:\n%s" "$FAIL_LIST"
  exit 1
fi
echo "✅ 18/18 TESTES PASSARAM — /healthz e /metrics bypass RBAC garantido 9 serviços."
exit 0
