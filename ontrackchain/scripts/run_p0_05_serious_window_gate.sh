#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${1:-${ROOT_DIR}/.env.staging.private}}"
WINDOW_ID="${WINDOW_ID:-${2:-stg-$(date -u +%Y-%m-%d)-serious-a}}"
MODE="${MODE:-${3:-baseline}}"
GOVERNANCE_WEEKLY_DIR="${GOVERNANCE_WEEKLY_DIR:-${4:-${ROOT_DIR}/docs/governance-weekly}}"
RUN_URL="${RUN_URL:-${5:-local://p0-05-serious-window}}"
OUTPUT_DIR="${OUTPUT_DIR:-}"
PAYLOAD_FILE="${PAYLOAD_FILE:-}"
LOCAL_RUN_NAME="${LOCAL_RUN_NAME:-P0-05 Serious Window Local Gate}"
WORKFLOW_NAME="${WORKFLOW_NAME:-P0-05 Serious Window Gate}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[p0-05] env file ausente: ${ENV_FILE}" >&2
  echo "[p0-05] forneca um env privado serio contendo insumos reais da janela" >&2
  exit 1
fi

cd "${ROOT_DIR}"

if [[ -n "${OUTPUT_DIR}" ]]; then
  mkdir -p "${OUTPUT_DIR}"
fi

if [[ -z "${PAYLOAD_FILE}" ]]; then
  if [[ -n "${OUTPUT_DIR}" ]]; then
    PAYLOAD_FILE="${OUTPUT_DIR}/p0-05-prepare-staging-window-output.json"
  else
    PAYLOAD_FILE="${ROOT_DIR}/artifacts/staging/checks/${WINDOW_ID}-prepare-staging-window-output.json"
  fi
fi

mkdir -p "$(dirname "${PAYLOAD_FILE}")"

echo "[p0-05] window_id=${WINDOW_ID}"
echo "[p0-05] mode=${MODE}"
echo "[p0-05] governance_weekly_dir=${GOVERNANCE_WEEKLY_DIR}"
echo "[p0-05] run_url=${RUN_URL}"
echo "[p0-05] payload_file=${PAYLOAD_FILE}"

python3 scripts/prepare_staging_window.py \
  --window-id "${WINDOW_ID}" \
  --mode "${MODE}" \
  --private-env-file "${ENV_FILE}" \
  --checks-dir "artifacts/staging/checks" \
  --dossiers-dir "artifacts/staging/dossiers" \
  --homologation-dir "artifacts/homologation" \
  --window-packet-dir "artifacts/staging" \
  --run > "${PAYLOAD_FILE}"

if [[ -n "${OUTPUT_DIR}" ]]; then
  cp "${PAYLOAD_FILE}" "${OUTPUT_DIR}/p0-05-payload.json"
fi

if [[ -n "${OUTPUT_DIR}" ]]; then
  python3 scripts/postprocess_staging_window_artifact.py \
    --payload-file "${PAYLOAD_FILE}" \
    --governance-weekly-dir "${GOVERNANCE_WEEKLY_DIR}" \
    --run-url "${RUN_URL}" \
    --run-name "${LOCAL_RUN_NAME}" \
    --workflow-name "${WORKFLOW_NAME}" | tee "${OUTPUT_DIR}/p0-05-postprocess.json"
else
  python3 scripts/postprocess_staging_window_artifact.py \
    --payload-file "${PAYLOAD_FILE}" \
    --governance-weekly-dir "${GOVERNANCE_WEEKLY_DIR}" \
    --run-url "${RUN_URL}" \
    --run-name "${LOCAL_RUN_NAME}" \
    --workflow-name "${WORKFLOW_NAME}"
fi

if [[ -n "${OUTPUT_DIR}" ]]; then
  signoff_file="${OUTPUT_DIR}/p0-05-staging-serious-window-signoff.md"
  python3 scripts/render_staging_window_signoff.py \
    --payload-file "${PAYLOAD_FILE}" \
    --output-file "${signoff_file}" \
    --run-name "${LOCAL_RUN_NAME}" \
    --run-url "${RUN_URL}" \
    --workflow-name "${WORKFLOW_NAME}"
fi

echo "[p0-05] janela seria concluida:"
echo "[p0-05] payload=${PAYLOAD_FILE}"
