#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_BASE_URL="${TEST_BASE_URL:-http://localhost:8080}"
AUTH_CONFIG_URL="${TEST_BASE_URL}/auth/config"
SUITE_NAME="${1:-}"

usage() {
  cat <<'EOF'
Uso:
  bash tests/e2e/run-stack-real.sh <suite>

Suites suportadas:
  api-consumer
  critical-path
  compliance-flows
  oidc-auth
  oidc-critical
EOF
}

wait_for_url() {
  local url="$1"
  local attempts="${2:-20}"

  for ((i = 1; i <= attempts; i += 1)); do
    if curl --silent --fail --output /dev/null "${url}"; then
      return 0
    fi
    sleep 1
  done

  echo "[stack-real] timeout aguardando ${url}" >&2
  return 1
}

read_auth_field() {
  local field_name="$1"

  curl --silent --fail "${AUTH_CONFIG_URL}" | node -e '
    const fieldName = process.argv[1];
    let data = "";
    process.stdin.on("data", (chunk) => {
      data += chunk;
    });
    process.stdin.on("end", () => {
      const parsed = JSON.parse(data);
      const value = parsed[fieldName] ?? parsed.oidc?.[fieldName] ?? "";
      process.stdout.write(String(value ?? ""));
    });
  ' "${field_name}"
}

ensure_base_ready() {
  wait_for_url "${TEST_BASE_URL}/"
  wait_for_url "${AUTH_CONFIG_URL}"
}

ensure_auth_mode() {
  local expected_mode="$1"
  local actual_mode

  actual_mode="$(read_auth_field "effective_auth_mode")"
  if [[ -z "${actual_mode}" ]]; then
    actual_mode="$(read_auth_field "auth_mode")"
  fi

  if [[ "${actual_mode}" != "${expected_mode}" ]]; then
    echo "[stack-real] ambiente incompatível: esperado auth mode '${expected_mode}', recebido '${actual_mode:-desconhecido}'" >&2
    exit 1
  fi
}

ensure_oidc_runtime() {
  ensure_auth_mode "oidc"

  local authorization_url
  local client_id
  local token_url

  authorization_url="$(read_auth_field "authorization_url")"
  client_id="$(read_auth_field "client_id")"
  token_url="$(read_auth_field "token_url")"

  if [[ -z "${authorization_url}" || -z "${client_id}" || -z "${token_url}" ]]; then
    echo "[stack-real] runtime OIDC incompleto em ${AUTH_CONFIG_URL}" >&2
    exit 1
  fi
}

run_playwright() {
  cd "${ROOT_DIR}"
  TEST_BASE_URL="${TEST_BASE_URL}" npx playwright test "$@"
}

if [[ -z "${SUITE_NAME}" ]]; then
  usage
  exit 1
fi

ensure_base_ready

case "${SUITE_NAME}" in
  api-consumer)
    run_playwright tests/e2e/api-consumer.spec.ts
    ;;
  critical-path)
    ensure_oidc_runtime
    run_playwright tests/e2e/critical-path.spec.ts
    ;;
  compliance-flows)
    run_playwright tests/e2e/compliance-flows.spec.ts
    ;;
  oidc-auth)
    ensure_oidc_runtime
    run_playwright tests/e2e/oidc-auth.spec.ts
    ;;
  oidc-critical)
    ensure_oidc_runtime
    run_playwright tests/e2e/oidc-auth.spec.ts tests/e2e/compliance-flows.spec.ts
    ;;
  *)
    usage
    exit 1
    ;;
esac
