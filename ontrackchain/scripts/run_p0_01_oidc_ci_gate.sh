#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${BASE_URL:-${1:-http://localhost:8080}}"
EXAMPLE_ENV_FILE="${EXAMPLE_ENV_FILE:-${ROOT_DIR}/.env.oidc-local.example}"
GENERATED_ENV_FILE="${GENERATED_ENV_FILE:-${ROOT_DIR}/ci-artifacts/.env.oidc-ci}"

if [[ ! -f "${EXAMPLE_ENV_FILE}" ]]; then
  echo "[p0-01-ci] env example ausente: ${EXAMPLE_ENV_FILE}" >&2
  exit 1
fi

mkdir -p "$(dirname "${GENERATED_ENV_FILE}")"
cp "${EXAMPLE_ENV_FILE}" "${GENERATED_ENV_FILE}"
chmod 600 "${GENERATED_ENV_FILE}"

cd "${ROOT_DIR}"
bash scripts/run_p0_01_oidc_local_gate.sh "${GENERATED_ENV_FILE}" "${BASE_URL}"
