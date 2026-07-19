#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${1:-${ROOT_DIR}/.env.staging.private}}"
WINDOW_ID="${WINDOW_ID:-${2:-stg-$(date -u +%Y-%m-%d)-reg}}"
CHECKS_DIR="${CHECKS_DIR:-${3:-${ROOT_DIR}/artifacts/staging/checks}}"
DOSSIERS_DIR="${DOSSIERS_DIR:-${4:-${ROOT_DIR}/artifacts/staging/dossiers}}"
INTERNAL_BASE_URL="${INTERNAL_BASE_URL:-${5:-http://localhost:8002}}"
PUBLIC_BASE_URL="${PUBLIC_BASE_URL:-${6:-http://localhost:8080}}"
OUTPUT_DIR="${OUTPUT_DIR:-}"
BUNDLE_OUTPUT_FILE="${CHECKS_DIR}/${WINDOW_ID}-regulatory-readiness-bundle.json"
BUNDLE_SUMMARY_FILE="${DOSSIERS_DIR}/${WINDOW_ID}-regulatory-readiness-bundle.md"

write_gate_summary() {
  local output_file="$1"
  python3 - "${output_file}" <<'PY'
import json
import os
import sys

summary = {
    "gate_id": "P0-04",
    "window_id": os.environ["WINDOW_ID"],
    "bundle_output_file": os.environ["BUNDLE_OUTPUT_FILE"],
    "bundle_summary_file": os.environ["BUNDLE_SUMMARY_FILE"],
    "execution_mode": "regulatory_bundle_generation_gate",
    "evidence_scope": "bundle json + summary markdown",
    "promotion_requires_manual_review": True,
    "status": "bundle_generated_for_review",
    "notes": [
        "Este gate consolida o bundle regulatorio para revisao manual.",
        "A geracao do bundle nao equivale, por si so, a readiness oficial sem insumos reais de P0-02 e P0-03."
    ]
}

with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(summary, handle, indent=2, ensure_ascii=True)
    handle.write("\n")
PY
}

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[p0-04] env file ausente: ${ENV_FILE}" >&2
  echo "[p0-04] forneca um env privado serio contendo insumos reais de P0-02/P0-03" >&2
  exit 1
fi

cd "${ROOT_DIR}"

set -a
source "${ENV_FILE}"
set +a

mkdir -p "${CHECKS_DIR}" "${DOSSIERS_DIR}"
if [[ -n "${OUTPUT_DIR}" ]]; then
  mkdir -p "${OUTPUT_DIR}"
fi

echo "[p0-04] window_id=${WINDOW_ID}"
echo "[p0-04] checks_dir=${CHECKS_DIR}"
echo "[p0-04] dossiers_dir=${DOSSIERS_DIR}"
echo "[p0-04] internal_base_url=${INTERNAL_BASE_URL}"
echo "[p0-04] public_base_url=${PUBLIC_BASE_URL}"

if [[ -n "${OUTPUT_DIR}" ]]; then
  python3 scripts/check_regulatory_window_readiness.py \
    --scope p0-04 \
    --private-env-file "${ENV_FILE}" \
    --ownership-file "docs/staging-env-ownership.md" | tee "${OUTPUT_DIR}/p0-04-regulatory-readiness.json"
else
  python3 scripts/check_regulatory_window_readiness.py \
    --scope p0-04 \
    --private-env-file "${ENV_FILE}" \
    --ownership-file "docs/staging-env-ownership.md"
fi

if [[ -n "${OUTPUT_DIR}" ]]; then
  python3 scripts/preflight_external_integrations.py | tee "${OUTPUT_DIR}/p0-04-preflight.json"
else
  python3 scripts/preflight_external_integrations.py
fi

set +e
python3 scripts/run_regulatory_readiness_bundle.py \
  --window-id "${WINDOW_ID}" \
  --private-env-file "${ENV_FILE}" \
  --checks-dir "${CHECKS_DIR}" \
  --internal-base-url "${INTERNAL_BASE_URL}" \
  --public-base-url "${PUBLIC_BASE_URL}" \
  > "${BUNDLE_OUTPUT_FILE}"
bundle_exit_code=$?
set -e

python3 scripts/render_regulatory_readiness_bundle.py \
  --bundle-file "${BUNDLE_OUTPUT_FILE}" \
  --output-file "${BUNDLE_SUMMARY_FILE}"

if [[ -n "${OUTPUT_DIR}" ]]; then
  cp "${BUNDLE_OUTPUT_FILE}" "${OUTPUT_DIR}/p0-04-regulatory-readiness-bundle.json"
  cp "${BUNDLE_SUMMARY_FILE}" "${OUTPUT_DIR}/p0-04-regulatory-readiness-bundle.md"
  write_gate_summary "${OUTPUT_DIR}/p0-04-gate-summary.json"
fi

if [[ ${bundle_exit_code} -ne 0 ]]; then
  echo "[p0-04] bundle regulatorio falhou: ${BUNDLE_OUTPUT_FILE}" >&2
  exit "${bundle_exit_code}"
fi

echo "[p0-04] bundle regulatorio concluido:"
echo "[p0-04] json=${BUNDLE_OUTPUT_FILE}"
echo "[p0-04] summary=${BUNDLE_SUMMARY_FILE}"
echo "[p0-04] bundle gerado para revisao manual; nao promover baseline sem prova real convergente de P0-02/P0-03."
