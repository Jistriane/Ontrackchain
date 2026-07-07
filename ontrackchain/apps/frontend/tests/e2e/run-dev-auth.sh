#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_BASE_URL="${TEST_BASE_URL:-http://localhost:8080}"
AUTH_CONFIG_URL="${TEST_BASE_URL}/auth/config"

wait_for_url() {
  local url="$1"
  local attempts="${2:-20}"

  for ((i = 1; i <= attempts; i += 1)); do
    if curl --silent --fail --output /dev/null "${url}"; then
      return 0
    fi
    sleep 1
  done

  echo "[dev-auth] timeout aguardando ${url}" >&2
  return 1
}

read_auth_mode() {
  curl --silent --fail "${AUTH_CONFIG_URL}" | node -e '
    let data = "";
    process.stdin.on("data", (chunk) => {
      data += chunk;
    });
    process.stdin.on("end", () => {
      const parsed = JSON.parse(data);
      process.stdout.write(String(parsed.effective_auth_mode ?? parsed.auth_mode ?? ""));
    });
  '
}

cd "${ROOT_DIR}"

wait_for_url "${TEST_BASE_URL}/"
wait_for_url "${AUTH_CONFIG_URL}"

AUTH_MODE="$(read_auth_mode)"
if [[ "${AUTH_MODE}" != "dev" ]]; then
  echo "[dev-auth] ambiente incompatível: esperado auth mode 'dev', recebido '${AUTH_MODE:-desconhecido}'" >&2
  exit 1
fi

TEST_BASE_URL="${TEST_BASE_URL}" npx playwright test tests/e2e/compliance-flows.spec.ts --grep "2FA"
