#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPLIANCE_CONTAINER="${COMPLIANCE_CONTAINER:-ontrackchain-compliance-api-1}"
API_KEY="${ONTRACKCHAIN_API_KEY:-otc_live_demo_key}"
DATABASE_URL="${DATABASE_URL:-postgresql://ontrackchain:ontrackchain@postgres:5432/ontrackchain}"
EU_URL="${COMPLIANCE_EU_SANCTIONS_SOURCE_URL:-}"
WINDOW_ID="${WINDOW_ID:-stg-2026-07-24-a}"

echo "Running staging window checks from inside Docker..."

# Run compliance provider runtime check
docker cp "${ROOT_DIR}/scripts/check_compliance_provider_runtime.py" "${COMPLIANCE_CONTAINER}:/tmp/check_runtime.py" >&2
RUNTIME_RESULT=$(docker exec "${COMPLIANCE_CONTAINER}" python /tmp/check_runtime.py \
  --internal-base-url http://localhost:8002 \
  --public-base-url http://traefik:80 \
  --api-key "${API_KEY}" 2>/dev/null)
docker exec "${COMPLIANCE_CONTAINER}" rm -f /tmp/check_runtime.py >&2

# Run EU sanctions sync check
docker cp "${ROOT_DIR}/scripts/check_sanctions_sync_status.py" "${COMPLIANCE_CONTAINER}:/tmp/check_sanctions.py" >&2
EU_RESULT=$(docker exec "${COMPLIANCE_CONTAINER}" python /tmp/check_sanctions.py \
  --database-url "${DATABASE_URL}" \
  --eu-override-url "${EU_URL}" 2>/dev/null)
docker exec "${COMPLIANCE_CONTAINER}" rm -f /tmp/check_sanctions.py >&2

# Save results to artifacts
ARTIFACTS_DIR="${ROOT_DIR}/artifacts/staging/checks"
mkdir -p "${ARTIFACTS_DIR}"
echo "$RUNTIME_RESULT" > "${ARTIFACTS_DIR}/${WINDOW_ID}-compliance-provider-runtime.json"
echo "$EU_RESULT" > "${ARTIFACTS_DIR}/${WINDOW_ID}-eu-sanctions-sync.json"

# Generate the regulatory readiness bundle
python3 << PYEOF
import json
from datetime import datetime, timezone

with open("${ARTIFACTS_DIR}/${WINDOW_ID}-compliance-provider-runtime.json") as f:
    runtime = json.load(f)
with open("${ARTIFACTS_DIR}/${WINDOW_ID}-eu-sanctions-sync.json") as f:
    eu = json.load(f)

runtime_ok = runtime.get('status') == 'ok'
eu_ok = eu.get('status') == 'ok'
bundle_status = 'ok' if runtime_ok and eu_ok else 'failed'

bundle = {
    'kind': 'regulatory_readiness_bundle',
    'status': bundle_status,
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'window_id': '${WINDOW_ID}',
    'steps': {
        'compliance_provider_runtime': {
            'status': runtime.get('status', 'failed'),
            'correlation': runtime.get('correlation', {}),
            'readiness': runtime.get('readiness', {}),
            'errors': runtime.get('errors', [])
        },
        'eu_sanctions_window': {
            'status': eu.get('status', 'failed'),
            'correlation': eu.get('correlation', {}),
            'readiness': eu.get('readiness', {}),
            'errors': eu.get('errors', [])
        }
    },
    'readiness': {
        'technical_status': 'ok' if bundle_status == 'ok' else 'blocked',
        'readiness_status': 'ready_for_homologation' if bundle_status == 'ok' else 'blocked',
        'blockers': [],
        'next_action': 'Executar homologation_external_evidence.py --mode regulatory e revisar a evidencia formal antes de promover P0-04.' if bundle_status == 'ok' else 'Corrigir as trilhas bloqueadas antes de gerar o bundle regulatorio.'
    }
}

if bundle_status != 'ok':
    bundle['readiness']['blockers'] = [
        'compliance_provider_runtime: ' + runtime.get('status', 'failed'),
        'eu_sanctions_window: ' + eu.get('status', 'failed')
    ]

with open("${ARTIFACTS_DIR}/${WINDOW_ID}-regulatory-readiness-bundle.json", 'w') as f:
    json.dump(bundle, f, ensure_ascii=True, indent=2)

print(json.dumps(bundle, ensure_ascii=True, indent=2))
PYEOF
