#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-ontrackchain}"
POSTGRES_DB="${POSTGRES_DB:-ontrackchain}"
BACKUP_DIR="${BACKUP_DIR:-artifacts/backups}"
TIMESTAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
OUTPUT_PATH="${1:-$BACKUP_DIR/${POSTGRES_DB}_${TIMESTAMP}.dump}"
MANIFEST_PATH="${BACKUP_MANIFEST_PATH:-${OUTPUT_PATH}.manifest.json}"

mkdir -p "$(dirname "$OUTPUT_PATH")"
mkdir -p "$(dirname "$MANIFEST_PATH")"

echo "[backup] postgres_service=$POSTGRES_SERVICE db=$POSTGRES_DB output=$OUTPUT_PATH"
docker compose exec -T "$POSTGRES_SERVICE" \
  pg_dump \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --format=custom \
  --no-owner \
  --no-privileges \
  > "$OUTPUT_PATH"

FILE_SIZE="$(wc -c < "$OUTPUT_PATH" | tr -d ' ')"
FILE_SHA256="$(sha256sum "$OUTPUT_PATH" | awk '{print $1}')"

python3 - "$MANIFEST_PATH" "$TIMESTAMP" "$POSTGRES_SERVICE" "$POSTGRES_DB" "$OUTPUT_PATH" "$FILE_SIZE" "$FILE_SHA256" <<'PY'
import json
import sys

manifest_path, timestamp, postgres_service, postgres_db, output_path, file_size, file_sha256 = sys.argv[1:]
payload = {
    "kind": "postgres_backup",
    "status": "ok",
    "timestamp_utc": timestamp,
    "postgres_service": postgres_service,
    "postgres_db": postgres_db,
    "backup_file": output_path,
    "backup_file_size_bytes": int(file_size),
    "backup_file_sha256": file_sha256,
    "format": "pg_dump_custom",
}
with open(manifest_path, "w", encoding="ascii") as fh:
    json.dump(payload, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY

echo "[backup] status=ok bytes=$FILE_SIZE sha256=$FILE_SHA256 file=$OUTPUT_PATH manifest=$MANIFEST_PATH timestamp_utc=$TIMESTAMP"
