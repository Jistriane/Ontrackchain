#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${1:-${ROOT_DIR}/.env.staging.private}}"
WINDOW_ID="${WINDOW_ID:-${2:-stg-$(date -u +%Y-%m-%d)-eu}}"
CHECKS_DIR="${CHECKS_DIR:-${3:-${ROOT_DIR}/artifacts/staging/checks}}"
REQUEST_ID="${REQUEST_ID:-${ONTRACKCHAIN_REGULATORY_EU_REQUEST_ID:-eu-window-$(date -u +%Y%m%d%H%M%S)}}"
OUTPUT_DIR="${OUTPUT_DIR:-}"

write_gate_summary() {
  local output_file="$1"
  python3 - "${output_file}" <<'PY'
import json
import os
import sys

summary = {
    "gate_id": "P0-03",
    "window_id": os.environ["WINDOW_ID"],
    "request_id": os.environ["REQUEST_ID"],
    "checks_dir": os.environ["CHECKS_DIR"],
    "execution_mode": "eu_window_sync_gate",
    "evidence_scope": "preflight + sanctions sync window + persisted checker",
    "promotion_requires_manual_review": True,
    "status": "window_executed_for_review",
    "notes": [
        "Este gate valida a janela tecnica do feed UE e persiste artefatos correlacionados.",
        "A promocao depende de confirmar source_url real, ACTIVE/SUCCESS e revisao humana da janela."
    ]
}

with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(summary, handle, indent=2, ensure_ascii=True)
    handle.write("\n")
PY
}

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[p0-03] env file ausente: ${ENV_FILE}" >&2
  echo "[p0-03] forneca um env privado serio com COMPLIANCE_EU_SANCTIONS_SOURCE_URL tokenizada" >&2
  exit 1
fi

cd "${ROOT_DIR}"

set -a
source "${ENV_FILE}"
set +a

if [[ -n "${OUTPUT_DIR}" ]]; then
  mkdir -p "${OUTPUT_DIR}"
fi

export ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE="${ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE:-disabled}"
export ONTRACKCHAIN_REGULATORY_EU_REQUEST_ID="${REQUEST_ID}"

echo "[p0-03] window_id=${WINDOW_ID}"
echo "[p0-03] request_id=${REQUEST_ID}"
echo "[p0-03] checks_dir=${CHECKS_DIR}"

if [[ -n "${OUTPUT_DIR}" ]]; then
  python3 scripts/check_regulatory_window_readiness.py \
    --scope p0-03 \
    --private-env-file "${ENV_FILE}" \
    --ownership-file "docs/staging-env-ownership.md" | tee "${OUTPUT_DIR}/p0-03-regulatory-readiness.json"
else
  python3 scripts/check_regulatory_window_readiness.py \
    --scope p0-03 \
    --private-env-file "${ENV_FILE}" \
    --ownership-file "docs/staging-env-ownership.md"
fi

if [[ -n "${OUTPUT_DIR}" ]]; then
  python3 scripts/preflight_external_integrations.py | tee "${OUTPUT_DIR}/p0-03-preflight.json"
else
  python3 scripts/preflight_external_integrations.py
fi

make rerun-compliance-worker

if [[ -n "${OUTPUT_DIR}" ]]; then
  python3 scripts/run_eu_sanctions_window.py \
    --window-id "${WINDOW_ID}" \
    --private-env-file "${ENV_FILE}" \
    --checks-dir "${CHECKS_DIR}" \
    --request-id "${REQUEST_ID}" | tee "${OUTPUT_DIR}/p0-03-eu-window.json"
else
  python3 scripts/run_eu_sanctions_window.py \
    --window-id "${WINDOW_ID}" \
    --private-env-file "${ENV_FILE}" \
    --checks-dir "${CHECKS_DIR}" \
    --request-id "${REQUEST_ID}"
fi

if [[ -n "${OUTPUT_DIR}" ]]; then
  python3 scripts/check_sanctions_sync_status.py --eu-window --request-id "${REQUEST_ID}" | tee "${OUTPUT_DIR}/p0-03-eu-checker.json"
else
  python3 scripts/check_sanctions_sync_status.py --eu-window --request-id "${REQUEST_ID}"
fi

if [[ -n "${OUTPUT_DIR}" ]]; then
  write_gate_summary "${OUTPUT_DIR}/p0-03-gate-summary.json"
fi

echo "[p0-03] janela tecnica concluida; promocao ainda exige revisao manual da source_url e do estado ACTIVE/SUCCESS."
