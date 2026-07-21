#!/bin/sh
set -e

if [ "$#" -eq 0 ]; then
  exec /app/infra/render/scripts/start-auth-service.sh
fi

if [ "$1" = "/app/infra/render/scripts/start-auth-service.sh" ] || [ "$1" = "start-auth-service.sh" ]; then
  exec /app/infra/render/scripts/start-auth-service.sh
fi

exec sh -c "$*"
