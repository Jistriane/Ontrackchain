#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPLIANCE_CONTAINER="${COMPLIANCE_CONTAINER:-ontrackchain-compliance-api-1}"
WINDOW_ID="${WINDOW_ID:-stg-2026-07-24-a}"

echo "Running full staging window from inside Docker..."

# Copy all required files to the container
docker cp "${ROOT_DIR}/.env.staging.private" "${COMPLIANCE_CONTAINER}:/tmp/.env.staging.private" >&2
docker cp "${ROOT_DIR}/.env.staging.example" "${COMPLIANCE_CONTAINER}:/tmp/.env.staging.example" >&2
docker cp "${ROOT_DIR}/docs/staging-env-ownership.md" "${COMPLIANCE_CONTAINER}:/tmp/docs/staging-env-ownership.md" >&2
docker cp "${ROOT_DIR}/scripts/" "${COMPLIANCE_CONTAINER}:/tmp/scripts/" >&2
docker cp "${ROOT_DIR}/artifacts/" "${COMPLIANCE_CONTAINER}:/tmp/artifacts/" >&2

# Run the staging window from inside the container
docker exec "${COMPLIANCE_CONTAINER}" bash -c "cd /tmp && python scripts/run_staging_window.py --window-id ${WINDOW_ID} --private-env-file /tmp/.env.staging.private" 2>&1

exit_code=$?

# Copy the artifacts back to the host
docker cp "${COMPLIANCE_CONTAINER}:/tmp/artifacts/staging/checks/" "${ROOT_DIR}/artifacts/staging/checks/" >&2 2>/dev/null || true
docker cp "${COMPLIANCE_CONTAINER}:/tmp/artifacts/staging/dossiers/" "${ROOT_DIR}/artifacts/staging/dossiers/" >&2 2>/dev/null || true
docker cp "${COMPLIANCE_CONTAINER}:/tmp/artifacts/homologation/" "${ROOT_DIR}/artifacts/homologation/" >&2 2>/dev/null || true

exit $exit_code
