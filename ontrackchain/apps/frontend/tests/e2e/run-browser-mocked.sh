#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRONTEND_PORT="${FRONTEND_PORT:-3100}"
FRONTEND_HOST="${FRONTEND_HOST:-localhost}"
TEST_BASE_URL="http://${FRONTEND_HOST}:${FRONTEND_PORT}"

cleanup() {
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
    wait "${FRONTEND_PID}" 2>/dev/null || true
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

  echo "[browser-mocked] timeout aguardando ${url}" >&2
  return 1
}

trap cleanup EXIT

cd "${ROOT_DIR}"

npx next dev -H 0.0.0.0 -p "${FRONTEND_PORT}" >/tmp/ontrackchain-browser-mocked-dev.log 2>&1 &
FRONTEND_PID=$!

wait_for_url "${TEST_BASE_URL}/login"

TEST_BASE_URL="${TEST_BASE_URL}" \
ONTRACKCHAIN_E2E_RESET_STATE=false \
npx playwright test \
  tests/e2e/audit-labels.spec.ts \
  tests/e2e/team-role-labels.spec.ts \
  tests/e2e/case-report-type-fallback.spec.ts \
  tests/e2e/reports-history.spec.ts \
  tests/e2e/evidence-custody.spec.ts \
  tests/e2e/operational-context-links.spec.ts \
  tests/e2e/timeline-workspace.spec.ts
