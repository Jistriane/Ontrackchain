#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRONTEND_PORT="${FRONTEND_PORT:-3100}"
DASHBOARD_MOCK_API_PORT="${DASHBOARD_MOCK_API_PORT:-4010}"
FRONTEND_HOST="${FRONTEND_HOST:-localhost}"
TEST_BASE_URL="http://${FRONTEND_HOST}:${FRONTEND_PORT}"
MOCK_API_URL="http://127.0.0.1:${DASHBOARD_MOCK_API_PORT}"

cleanup() {
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
    wait "${FRONTEND_PID}" 2>/dev/null || true
  fi

  if [[ -n "${MOCK_PID:-}" ]] && kill -0 "${MOCK_PID}" 2>/dev/null; then
    kill "${MOCK_PID}" 2>/dev/null || true
    wait "${MOCK_PID}" 2>/dev/null || true
  fi
}

wait_for_url() {
  local url="$1"
  local attempts="${2:-60}"

  for ((i = 1; i <= attempts; i += 1)); do
    if curl --silent --fail --output /dev/null "${url}"; then
      return 0
    fi
    sleep 1
  done

  echo "[alerts-dashboard-context] timeout aguardando ${url}" >&2
  return 1
}

trap cleanup EXIT

cd "${ROOT_DIR}"

DASHBOARD_MOCK_API_PORT="${DASHBOARD_MOCK_API_PORT}" node tests/e2e/mock-dashboard-api.cjs &
MOCK_PID=$!

wait_for_url "${MOCK_API_URL}/api/v1/investigation/admin/operations"

INTERNAL_API_BASE_URL="${MOCK_API_URL}" \
NEXT_PUBLIC_API_BASE_URL="${MOCK_API_URL}" \
npx next dev -H 0.0.0.0 -p "${FRONTEND_PORT}" >/tmp/ontrackchain-alerts-dashboard-dev.log 2>&1 &
FRONTEND_PID=$!

wait_for_url "${TEST_BASE_URL}/login"

TEST_BASE_URL="${TEST_BASE_URL}" \
ONTRACKCHAIN_E2E_RESET_STATE=false \
npx playwright test tests/e2e/alerts-dashboard-context-links.spec.ts
