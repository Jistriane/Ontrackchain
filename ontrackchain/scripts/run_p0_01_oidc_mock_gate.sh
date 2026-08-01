#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${1:-${ROOT_DIR}/.env.oidc-mock}}"
BASE_URL="${BASE_URL:-${2:-http://localhost:8080}}"
AUTH_CONFIG_URL="${BASE_URL%/}/auth/config"
OUT_DIR="${OUT_DIR:-${ROOT_DIR}/tmp/gates/p0-01-oidc-mock}"
AUTO_TEARDOWN="${AUTO_TEARDOWN:-}"

COMPOSE_ARGS=(-f docker-compose.yml --env-file "${ENV_FILE}")

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[p0-01-mock] env file ausente: ${ENV_FILE}" >&2
  echo "[p0-01-mock] copie ${ROOT_DIR}/.env.oidc-mock.example para ${ROOT_DIR}/.env.oidc-mock e ajuste os valores locais" >&2
  exit 1
fi

cd "${ROOT_DIR}"

set -a
source "${ENV_FILE}"
set +a

mkdir -p "${OUT_DIR}"

teardown_stack() {
  docker compose "${COMPOSE_ARGS[@]}" down --remove-orphans >/dev/null 2>&1 || true
}

auto_teardown_enabled() {
  local normalized
  normalized="$(echo "${AUTO_TEARDOWN}" | tr '[:upper:]' '[:lower:]' | xargs)"
  if [[ -n "${normalized}" ]]; then
    [[ "${normalized}" == "1" || "${normalized}" == "true" || "${normalized}" == "yes" || "${normalized}" == "on" ]]
    return $?
  fi
  normalized="$(echo "${CI:-}" | tr '[:upper:]' '[:lower:]' | xargs)"
  [[ "${normalized}" == "1" || "${normalized}" == "true" || "${normalized}" == "yes" || "${normalized}" == "on" ]]
}

if auto_teardown_enabled; then
  trap teardown_stack EXIT
fi

print_runtime_diagnostics() {
  echo "[p0-01-mock] diagnostico externo ${AUTH_CONFIG_URL}" >&2
  curl --silent --show-error "${AUTH_CONFIG_URL}" >&2 || true
  echo >&2

  echo "[p0-01-mock] diagnostico oidc discovery" >&2
  curl --silent --show-error -H "Host: oidc.localhost" "${BASE_URL%/}/.well-known/openid-configuration" >&2 || true
  echo >&2

  echo "[p0-01-mock] diagnostico interno auth-service /auth/config" >&2
  docker compose "${COMPOSE_ARGS[@]}" exec -T auth-service python -c '
import json
from urllib.request import urlopen

with urlopen("http://localhost:9000/auth/config", timeout=10) as response:
    payload = json.load(response)
print(json.dumps(payload, ensure_ascii=True))
' >&2 || true
  echo >&2

  echo "[p0-01-mock] diagnostico frontend env" >&2
  docker compose "${COMPOSE_ARGS[@]}" exec -T frontend sh -lc \
    "env | grep -E 'APP_ENV|AUTH_MODE|DEV_AUTH_ENABLED|NEXT_PUBLIC_APP_ENV|NEXT_PUBLIC_AUTH_MODE|NEXT_PUBLIC_DEV_AUTH_ENABLED|INTERNAL_AUTH_BASE_URL|INTERNAL_OIDC_BASE_URL' | sort" >&2 || true
}

wait_for_auth_config() {
  local attempts="${1:-45}"

  for ((i = 1; i <= attempts; i += 1)); do
    if curl --silent --show-error --fail --output /dev/null "${AUTH_CONFIG_URL}"; then
      return 0
    fi
    sleep 2
  done

  echo "[p0-01-mock] auth config nao ficou pronto: ${AUTH_CONFIG_URL}" >&2
  print_runtime_diagnostics
  return 1
}

docker compose "${COMPOSE_ARGS[@]}" up -d --build traefik postgres redis mock-oidc auth-service investigation-api frontend

wait_for_auth_config 60

ONTRACKCHAIN_BASE_URL="${BASE_URL}" \
ONTRACKCHAIN_EXPECTED_AUTH_MODE="oidc" \
ONTRACKCHAIN_EXPECTED_EFFECTIVE_AUTH_MODE="oidc" \
ONTRACKCHAIN_EXPECTED_APP_ENV="${APP_ENV:-staging}" \
ONTRACKCHAIN_EXPECTED_DEV_AUTH_ENABLED="false" \
ONTRACKCHAIN_EXPECTED_OIDC_PROVIDER="mock" \
ONTRACKCHAIN_EXPECTED_OIDC_ORG_CLAIM="${OIDC_ORG_CLAIM:-org}" \
ONTRACKCHAIN_EXPECTED_OIDC_PLAN_CLAIM="${OIDC_PLAN_CLAIM:-plan}" \
ONTRACKCHAIN_EXPECTED_OIDC_ROLE_CLAIM="${OIDC_ROLE_CLAIM:-otk_role}" \
python3 scripts/smoke_auth_oidc_mode.py > "${OUT_DIR}/smoke_auth_config.json" || {
  print_runtime_diagnostics
  exit 1
}

python3 scripts/smoke_mock_oidc_forwardauth_rbac.py \
  --base-url "${BASE_URL}" \
  --output-file "${OUT_DIR}/smoke_forwardauth_rbac.json" || {
  print_runtime_diagnostics
  exit 1
}

python3 scripts/run_oidc_playwright_critical.py \
  --base-url "${BASE_URL}" \
  --suite-command "npm run test:e2e:oidc-mock-critical" \
  > "${OUT_DIR}/playwright_oidc_mock_critical.json" || {
  print_runtime_diagnostics
  exit 1
}
