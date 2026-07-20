#!/bin/sh
set -eu

python3 /app/infra/render/scripts/apply_postgres_bootstrap.py
PORT_TO_USE="${PORT:-9000}"
exec uvicorn auth_service.main:app --host 0.0.0.0 --port "$PORT_TO_USE"
