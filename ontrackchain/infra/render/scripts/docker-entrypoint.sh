#!/bin/sh
set -e

if [ "$#" -eq 0 ]; then
  exec /app/infra/render/scripts/start-auth-service.sh
fi

exec sh -c "$*"
