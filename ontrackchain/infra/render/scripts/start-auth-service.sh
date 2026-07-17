#!/bin/sh
set -eu

python3 /app/infra/render/scripts/apply_postgres_bootstrap.py
exec uvicorn auth_service.main:app --host 0.0.0.0 --port 9000
