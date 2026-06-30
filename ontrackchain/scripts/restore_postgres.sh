#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ $# -lt 1 ]]; then
  echo "uso: bash scripts/restore_postgres.sh <arquivo.dump>" >&2
  exit 1
fi

BACKUP_FILE="$1"
if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "arquivo nao encontrado: $BACKUP_FILE" >&2
  exit 1
fi

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-ontrackchain}"
POSTGRES_DB="${POSTGRES_DB:-ontrackchain}"
RESTORE_TARGET_DB="${RESTORE_TARGET_DB:-${POSTGRES_DB}_restore_check}"
MANIFEST_PATH="${RESTORE_MANIFEST_PATH:-${BACKUP_FILE}.restore.${RESTORE_TARGET_DB}.manifest.json}"
SOURCE_FILE_SIZE="$(wc -c < "$BACKUP_FILE" | tr -d ' ')"
SOURCE_FILE_SHA256="$(sha256sum "$BACKUP_FILE" | awk '{print $1}')"
START_TIMESTAMP_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

mkdir -p "$(dirname "$MANIFEST_PATH")"

if [[ "$RESTORE_TARGET_DB" == "$POSTGRES_DB" ]] && [[ "${ONTRACKCHAIN_RESTORE_CONFIRM:-}" != "OVERWRITE_MAIN_DB" ]]; then
  echo "restore no banco principal bloqueado; use RESTORE_TARGET_DB separado ou ONTRACKCHAIN_RESTORE_CONFIRM=OVERWRITE_MAIN_DB" >&2
  exit 1
fi

START_EPOCH="$(date +%s)"
echo "[restore] postgres_service=$POSTGRES_SERVICE source=$BACKUP_FILE target_db=$RESTORE_TARGET_DB"

docker compose exec -T "$POSTGRES_SERVICE" \
  psql \
  --username "$POSTGRES_USER" \
  --dbname postgres \
  --set ON_ERROR_STOP=1 \
  --command "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${RESTORE_TARGET_DB}' AND pid <> pg_backend_pid();" \
  --command "DROP DATABASE IF EXISTS \"${RESTORE_TARGET_DB}\";" \
  --command "CREATE DATABASE \"${RESTORE_TARGET_DB}\";"

cat "$BACKUP_FILE" | docker compose exec -T "$POSTGRES_SERVICE" \
  pg_restore \
  --username "$POSTGRES_USER" \
  --dbname "$RESTORE_TARGET_DB" \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges

TABLE_COUNT="$(
  docker compose exec -T "$POSTGRES_SERVICE" \
    psql \
    --username "$POSTGRES_USER" \
    --dbname "$RESTORE_TARGET_DB" \
    --tuples-only \
    --no-align \
    --command "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" \
    | tr -d '[:space:]'
)"

END_EPOCH="$(date +%s)"
RTO_SECONDS="$((END_EPOCH - START_EPOCH))"
END_TIMESTAMP_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

python - "$MANIFEST_PATH" "$START_TIMESTAMP_UTC" "$END_TIMESTAMP_UTC" "$POSTGRES_SERVICE" "$POSTGRES_DB" "$RESTORE_TARGET_DB" "$BACKUP_FILE" "$SOURCE_FILE_SIZE" "$SOURCE_FILE_SHA256" "$TABLE_COUNT" "$RTO_SECONDS" <<'PY'
import json
import sys

(
    manifest_path,
    started_at,
    finished_at,
    postgres_service,
    source_db,
    target_db,
    backup_file,
    source_file_size,
    source_file_sha256,
    table_count,
    rto_seconds,
) = sys.argv[1:]

payload = {
    "kind": "postgres_restore",
    "status": "ok",
    "started_at_utc": started_at,
    "finished_at_utc": finished_at,
    "postgres_service": postgres_service,
    "source_db": source_db,
    "target_db": target_db,
    "source_backup_file": backup_file,
    "source_backup_file_size_bytes": int(source_file_size),
    "source_backup_file_sha256": source_file_sha256,
    "public_table_count": int(table_count),
    "rto_seconds": int(rto_seconds),
    "restore_mode": "isolated_db" if target_db != source_db else "main_db_overwrite",
}
with open(manifest_path, "w", encoding="ascii") as fh:
    json.dump(payload, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY

echo "[restore] status=ok target_db=$RESTORE_TARGET_DB public_tables=$TABLE_COUNT rto_seconds=$RTO_SECONDS manifest=$MANIFEST_PATH"
