#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${1:-${ROOT_DIR}/.env.oidc-local}}"
BASE_URL="${BASE_URL:-${2:-http://localhost:8080}}"
AUTH_CONFIG_URL="${BASE_URL%/}/auth/config"
COMPOSE_ARGS=(-f docker-compose.yml -f docker-compose.oidc-local.yml --env-file "${ENV_FILE}" --profile oidc)

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[p0-01] env file ausente: ${ENV_FILE}" >&2
  echo "[p0-01] copie ${ROOT_DIR}/.env.oidc-local.example para ${ROOT_DIR}/.env.oidc-local e ajuste os valores locais" >&2
  exit 1
fi

cd "${ROOT_DIR}"

set -a
source "${ENV_FILE}"
set +a

print_runtime_diagnostics() {
  echo "[p0-01] diagnostico externo ${AUTH_CONFIG_URL}" >&2
  curl --silent --show-error "${AUTH_CONFIG_URL}" >&2 || true
  echo >&2

  echo "[p0-01] diagnostico interno auth-service /auth/config" >&2
  docker compose "${COMPOSE_ARGS[@]}" exec -T auth-service python -c '
import json
from urllib.request import urlopen

with urlopen("http://localhost:9000/auth/config", timeout=10) as response:
    payload = json.load(response)
print(json.dumps(payload, ensure_ascii=True))
' >&2 || true
  echo >&2

  echo "[p0-01] diagnostico frontend env" >&2
  docker compose "${COMPOSE_ARGS[@]}" exec -T frontend sh -lc \
    "env | grep -E 'APP_ENV|AUTH_MODE|DEV_AUTH_ENABLED|NEXT_PUBLIC_APP_ENV|NEXT_PUBLIC_AUTH_MODE|NEXT_PUBLIC_DEV_AUTH_ENABLED|INTERNAL_AUTH_BASE_URL|INTERNAL_KEYCLOAK_BASE_URL' | sort" >&2 || true
}

wait_for_auth_config() {
  local attempts="${1:-30}"

  for ((i = 1; i <= attempts; i += 1)); do
    if curl --silent --show-error --fail --output /dev/null "${AUTH_CONFIG_URL}"; then
      return 0
    fi
    sleep 2
  done

  echo "[p0-01] auth config nao ficou pronto: ${AUTH_CONFIG_URL}" >&2
  print_runtime_diagnostics
  return 1
}

bash scripts/start_oidc_local.sh "${ENV_FILE}"

python3 scripts/preflight_oidc_serious_env.py
wait_for_auth_config 45

ONTRACKCHAIN_BASE_URL="${BASE_URL}" \
ONTRACKCHAIN_EXPECTED_AUTH_MODE="oidc" \
ONTRACKCHAIN_EXPECTED_EFFECTIVE_AUTH_MODE="oidc" \
ONTRACKCHAIN_EXPECTED_APP_ENV="staging" \
ONTRACKCHAIN_EXPECTED_DEV_AUTH_ENABLED="false" \
ONTRACKCHAIN_EXPECTED_OIDC_PROVIDER="${OIDC_PROVIDER:-keycloak}" \
ONTRACKCHAIN_EXPECTED_OIDC_ORG_CLAIM="${OIDC_ORG_CLAIM:-org}" \
ONTRACKCHAIN_EXPECTED_OIDC_PLAN_CLAIM="${OIDC_PLAN_CLAIM:-plan}" \
ONTRACKCHAIN_EXPECTED_OIDC_ROLE_CLAIM="${OIDC_ROLE_CLAIM:-otk_role}" \
python3 scripts/smoke_auth_oidc_mode.py || {
  print_runtime_diagnostics
  exit 1
}

python3 scripts/run_oidc_playwright_critical.py --base-url "${BASE_URL}" || {
  print_runtime_diagnostics
  exit 1
}
