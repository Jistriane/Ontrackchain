#!/bin/sh
set -e

if [ "$#" -eq 0 ]; then
  exec /app/infra/render/scripts/start-auth-service.sh
fi

case "$*" in
  *start-auth-service.sh*|*apply_postgres_bootstrap*|*auth_service.main:app*)
    exec /app/infra/render/scripts/start-auth-service.sh
    ;;
esac

exec sh -c "$*"
