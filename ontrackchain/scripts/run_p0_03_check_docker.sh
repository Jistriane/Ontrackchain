#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPLIANCE_CONTAINER="${COMPLIANCE_CONTAINER:-ontrackchain-compliance-api-1}"
DATABASE_URL="${DATABASE_URL:-postgresql://ontrackchain:ontrackchain@postgres:5432/ontrackchain}"
EU_OVERRIDE_URL="${COMPLIANCE_EU_SANCTIONS_SOURCE_URL:-}"

# Copy check script to container
docker cp "${ROOT_DIR}/scripts/check_sanctions_sync_status.py" "${COMPLIANCE_CONTAINER}:/tmp/check_sanctions.py" >&2

# Build args
DB_ARGS="--database-url ${DATABASE_URL}"
if [ -n "$EU_OVERRIDE_URL" ]; then
  DB_ARGS="${DB_ARGS} --eu-override-url ${EU_OVERRIDE_URL}"
fi

# Run check from inside the container
docker exec "${COMPLIANCE_CONTAINER}" python /tmp/check_sanctions.py ${DB_ARGS}

exit_code=$?

# Clean up
docker exec "${COMPLIANCE_CONTAINER}" rm -f /tmp/check_sanctions.py >&2

exit $exit_code
