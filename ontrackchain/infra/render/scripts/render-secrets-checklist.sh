#!/usr/bin/env bash
# OnTrackChain Render Deploy — Validação de secrets obrigatórios
# Uso: bash infra/render/scripts/render-secrets-checklist.sh (no dashboard terminal ou deploy hook)

set -euo pipefail

REQUIRED_SECRETS=(
  POSTGRES_PASSWORD
  JWT_HS256_SECRET
  MFA_TOTP_SECRET
  KEYCLOAK_ADMIN_PASSWORD
  KEYCLOAK_B2B_CLIENT_SECRET
  KEYCLOAK_SYSTEM_USER_PASSWORD
  KEYCLOAK_KMD_TESTER_PASSWORD
  KEYCLOAK_JIBSO_ADMIN_PASSWORD
  KEYCLOAK_AUDITOR_PASSWORD
  KEYCLOAK_ANALYST_PASSWORD
  KEYCLOAK_VIEWER_PASSWORD
  KEYCLOAK_SEM_ORG_PASSWORD
  KEYCLOAK_DB_PASSWORD
  AUTH_DB_PASSWORD
  CASE_DB_PASSWORD
  INV_DB_PASSWORD
  BILLING_DB_PASSWORD
  COMPLIANCE_DB_PASSWORD
  COUNTERPARTY_DB_PASSWORD
  NOTIFICATION_DB_PASSWORD
  AUDIT_DB_PASSWORD
  ENTERPRISE_DB_PASSWORD
  SANCTIONS_DB_PASSWORD
  RISK_DB_PASSWORD
  MONITORING_DB_PASSWORD
  AI_DB_PASSWORD
  REPORTING_DB_PASSWORD
  EVENT_DB_PASSWORD
  TEAM_DB_PASSWORD
  EVIDENCE_DB_PASSWORD
  BLOCKCHAIN_DB_PASSWORD
  ANTHROPIC_API_KEY
  GROQ_API_KEY
  VOYAGE_API_KEY
  INVESTIGATION_INTERNAL_WORKER_TOKEN
  INVESTIGATION_RPC_PRIMARY_URL
  COMPLIANCE_TRM_API_KEY
  OPENSANCTIONS_API_KEY
  ALERTMANAGER_WEBHOOK_BEARER_TOKEN
  GRAFANA_ADMIN_PASSWORD
)

OPTIONAL_SECRETS=(
  STRIPE_PUBLISHABLE_KEY
  STRIPE_SECRET_KEY
  STRIPE_WEBHOOK_SECRET
  RENDER_API_KEY
  RENDER_BLUEPRINT_ID
  RENDER_OWNER_ID
)

REQUIRED_MIN_LENGTH=12

declare -a MISSING=()
declare -a WEAK=()
declare -a OK=()

for var in "${REQUIRED_SECRETS[@]}"; do
  val="${!var:-}"
  if [[ -z "$val" ]]; then
    MISSING+=("$var")
  else
    [[ ${#val} -ge $REQUIRED_MIN_LENGTH ]] && OK+=("$var") || WEAK+=("$var")
  fi
done

echo "================================================================================"
echo " OnTrackChain — Render Secrets Checklist  (REQUIRED=${#REQUIRED_SECRETS[@]})"
echo "================================================================================"
echo ""
echo "✅ OK (${#OK[@]}/${#REQUIRED_SECRETS[@]}) — variáveis preenchidas e >= ${REQUIRED_MIN_LENGTH} chars"
if [[ ${#OK[@]} -gt 0 ]]; then
  for v in "${OK[@]}"; do echo "    · $v"; done
fi
echo ""
echo "⚠️  FRACO ou TAMANHO CURTO (${#WEAK[@]})"
if [[ ${#WEAK[@]} -gt 0 ]]; then
  for v in "${WEAK[@]}"; do echo "    · $v → precisa ter >= ${REQUIRED_MIN_LENGTH} chars"; done
fi
echo ""
echo "🚨 FALTANDO (${#MISSING[@]}) — NÃO FAÇA DEPLOY SEM PREENCHER NO RENDER ENV GROUP"
if [[ ${#MISSING[@]} -gt 0 ]]; then
  for v in "${MISSING[@]}"; do echo "    · SYNC:FALSE → $v"; done
  echo ""
  exit 1
fi

echo ""
echo "🎯 Resultado: ${#OK[@]}/${#REQUIRED_SECRETS[@]} secrets presentes + tamanho mínimo ok. Deploy seguro prosseguir."
echo ""
echo "ℹ️  Opcionais (staging pode deixar em branco = fallbacks FREE ilimitado ou FREE tier providers):"
for var in "${OPTIONAL_SECRETS[@]}"; do
  val="${!var:-}"
  if [[ -n "$val" ]]; then
    echo "    · $var = ********${val: -4} (OK)"
  else
    echo "    · $var = VAZIO (fallback ativado)"
  fi
done
