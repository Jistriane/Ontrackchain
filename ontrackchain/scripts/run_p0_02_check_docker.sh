#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPLIANCE_CONTAINER="${COMPLIANCE_CONTAINER:-ontrackchain-compliance-api-1}"
API_KEY="${ONTRACKCHAIN_API_KEY:-otc_live_demo_key}"
INTERNAL_BASE_URL="${INTERNAL_BASE_URL:-http://localhost:8002}"
PUBLIC_BASE_URL="${PUBLIC_BASE_URL:-http://traefik:80}"
EXPECTED_PROVIDER="${COMPLIANCE_RISK_PROVIDER:-opensanctions}"

# Copy check script to container
docker cp "${ROOT_DIR}/scripts/check_compliance_provider_runtime.py" "${COMPLIANCE_CONTAINER}:/tmp/check.py" >&2

# Run check from inside the container (stdout = JSON, stderr = diagnostics)
docker exec "${COMPLIANCE_CONTAINER}" python /tmp/check.py \
  --internal-base-url "${INTERNAL_BASE_URL}" \
  --public-base-url "${PUBLIC_BASE_URL}" \
  --api-key "${API_KEY}" \
  --expected-provider "${EXPECTED_PROVIDER}"

exit_code=$?

# Clean up
docker exec "${COMPLIANCE_CONTAINER}" rm -f /tmp/check.py >&2

exit $exit_code
