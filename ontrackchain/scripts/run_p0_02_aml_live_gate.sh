#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${1:-${ROOT_DIR}/.env.staging.private}}"
INTERNAL_BASE_URL="${INTERNAL_BASE_URL:-${2:-http://localhost:8002}}"
PUBLIC_BASE_URL="${PUBLIC_BASE_URL:-${3:-http://localhost:8080}}"
REQUEST_ID="${REQUEST_ID:-${ONTRACKCHAIN_REGULATORY_COMPLIANCE_REQUEST_ID:-compliance-runtime-$(date -u +%Y%m%d%H%M%S)}}"
OUTPUT_DIR="${OUTPUT_DIR:-}"

write_gate_summary() {
  local output_file="$1"
  python3 - "${output_file}" <<'PY'
import json
import os
import sys

summary = {
    "gate_id": "P0-02",
    "request_id": os.environ["REQUEST_ID"],
    "internal_base_url": os.environ["INTERNAL_BASE_URL"],
    "public_base_url": os.environ["PUBLIC_BASE_URL"],
    "execution_mode": "preparatory_runtime_gate",
    "evidence_scope": "preflight + runtime checker + smoke runtime",
    "formal_evidence_generated": False,
    "promotion_requires_manual_review": True,
    "next_required_step": "python3 scripts/homologation_external_evidence.py --mode compliance",
    "status": "prepared_for_homologation",
    "notes": [
        "Este gate valida convergencia tecnica do runtime AML/KYT live.",
        "O sucesso deste gate nao substitui a homologacao externa nem a revisao humana da evidencia."
    ]
}

with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(summary, handle, indent=2, ensure_ascii=True)
    handle.write("\n")
PY
}

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[p0-02] env file ausente: ${ENV_FILE}" >&2
  echo "[p0-02] forneca um env privado serio com credenciais AML/KYT live" >&2
  exit 1
fi

cd "${ROOT_DIR}"

set -a
source "${ENV_FILE}"
set +a

if [[ -n "${OUTPUT_DIR}" ]]; then
  mkdir -p "${OUTPUT_DIR}"
fi

export ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE="${ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE:-live}"
export ONTRACKCHAIN_EXPECT_RPC_MODE="${ONTRACKCHAIN_EXPECT_RPC_MODE:-disabled}"
export ONTRACKCHAIN_REGULATORY_COMPLIANCE_REQUEST_ID="${REQUEST_ID}"
export ONTRACKCHAIN_HOMOLOGATION_COMPLIANCE_REQUEST_ID="${ONTRACKCHAIN_HOMOLOGATION_COMPLIANCE_REQUEST_ID:-${REQUEST_ID}}"

echo "[p0-02] request_id=${REQUEST_ID}"
echo "[p0-02] internal_base_url=${INTERNAL_BASE_URL}"
echo "[p0-02] public_base_url=${PUBLIC_BASE_URL}"

if [[ -n "${OUTPUT_DIR}" ]]; then
  python3 scripts/check_regulatory_window_readiness.py \
    --scope p0-02 \
    --private-env-file "${ENV_FILE}" \
    --ownership-file "docs/staging-env-ownership.md" | tee "${OUTPUT_DIR}/p0-02-regulatory-readiness.json"
else
  python3 scripts/check_regulatory_window_readiness.py \
    --scope p0-02 \
    --private-env-file "${ENV_FILE}" \
    --ownership-file "docs/staging-env-ownership.md"
fi

if [[ -n "${OUTPUT_DIR}" ]]; then
  python3 scripts/preflight_external_integrations.py | tee "${OUTPUT_DIR}/p0-02-preflight.json"
else
  python3 scripts/preflight_external_integrations.py
fi

if [[ -n "${OUTPUT_DIR}" ]]; then
  python3 scripts/check_compliance_provider_runtime.py \
    --internal-base-url "${INTERNAL_BASE_URL}" \
    --public-base-url "${PUBLIC_BASE_URL}" \
    --request-id "${REQUEST_ID}" | tee "${OUTPUT_DIR}/p0-02-compliance-runtime.json"
else
  python3 scripts/check_compliance_provider_runtime.py \
    --internal-base-url "${INTERNAL_BASE_URL}" \
    --public-base-url "${PUBLIC_BASE_URL}" \
    --request-id "${REQUEST_ID}"
fi

if [[ -n "${OUTPUT_DIR}" ]]; then
  python3 scripts/smoke_runtime.py | tee "${OUTPUT_DIR}/p0-02-smoke-runtime.json"
else
  python3 scripts/smoke_runtime.py
fi

if [[ -n "${OUTPUT_DIR}" ]]; then
  write_gate_summary "${OUTPUT_DIR}/p0-02-gate-summary.json"
fi

echo "[p0-02] gate preparatorio concluido; ainda nao equivale a homologacao formal."
echo "[p0-02] para evidencia formal e correlacao externa, execute:"
echo "[p0-02] python3 scripts/homologation_external_evidence.py --mode compliance"
