#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPLIANCE_CONTAINER="${COMPLIANCE_CONTAINER:-ontrackchain-compliance-api-1}"
API_KEY="${ONTRACKCHAIN_API_KEY:-otc_live_demo_key}"
DATABASE_URL="${DATABASE_URL:-postgresql://ontrackchain:ontrackchain@postgres:5432/ontrackchain}"
EU_URL="${COMPLIANCE_EU_SANCTIONS_SOURCE_URL:-}"

echo '{"kind":"regulatory_readiness_bundle","status":"ok","steps":{}}' | python3 -c "
import sys, json

# Step 1: Compliance Provider Runtime
print('Running compliance provider runtime check...', file=sys.stderr)
" 2>&1

# Run compliance provider runtime check
docker cp "${ROOT_DIR}/scripts/check_compliance_provider_runtime.py" "${COMPLIANCE_CONTAINER}:/tmp/check_runtime.py" >&2
RUNTIME_RESULT=$(docker exec "${COMPLIANCE_CONTAINER}" python /tmp/check_runtime.py \
  --internal-base-url http://localhost:8002 \
  --public-base-url http://traefik:80 \
  --api-key "${API_KEY}" 2>/dev/null)
docker exec "${COMPLIANCE_CONTAINER}" rm -f /tmp/check_runtime.py >&2

RUNTIME_STATUS=$(echo "$RUNTIME_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','failed'))")
echo "Compliance runtime: $RUNTIME_STATUS" >&2

# Run EU sanctions sync check
docker cp "${ROOT_DIR}/scripts/check_sanctions_sync_status.py" "${COMPLIANCE_CONTAINER}:/tmp/check_sanctions.py" >&2
EU_RESULT=$(docker exec "${COMPLIANCE_CONTAINER}" python /tmp/check_sanctions.py \
  --database-url "${DATABASE_URL}" \
  --eu-override-url "${EU_URL}" 2>/dev/null)
docker exec "${COMPLIANCE_CONTAINER}" rm -f /tmp/check_sanctions.py >&2

EU_STATUS=$(echo "$EU_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','failed'))")
echo "EU sanctions: $EU_STATUS" >&2

# Build bundle
BUNDLE_STATUS="ok"
if [ "$RUNTIME_STATUS" != "ok" ] || [ "$EU_STATUS" != "ok" ]; then
  BUNDLE_STATUS="failed"
fi

# Output JSON bundle
python3 -c "
import sys, json
from datetime import datetime, timezone

runtime = json.loads('''${RUNTIME_RESULT}''')
eu = json.loads('''${EU_RESULT}''')

bundle = {
    'kind': 'regulatory_readiness_bundle',
    'status': '${BUNDLE_STATUS}',
    'generated_at': datetime.now(timezone.utc).isoformat(),
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
        'technical_status': 'ok' if '${BUNDLE_STATUS}' == 'ok' else 'blocked',
        'readiness_status': 'ready_for_homologation' if '${BUNDLE_STATUS}' == 'ok' else 'blocked',
        'blockers': [],
        'next_action': 'Executar homologation_external_evidence.py --mode regulatory e revisar a evidencia formal antes de promover P0-04.' if '${BUNDLE_STATUS}' == 'ok' else 'Corrigir as trilhas bloqueadas antes de gerar o bundle regulatorio.'
    }
}

if '${BUNDLE_STATUS}' != 'ok':
    bundle['readiness']['blockers'] = [
        'compliance_provider_runtime: ' + runtime.get('status', 'failed'),
        'eu_sanctions_window: ' + eu.get('status', 'failed')
    ]

print(json.dumps(bundle, ensure_ascii=True, indent=2))
"
