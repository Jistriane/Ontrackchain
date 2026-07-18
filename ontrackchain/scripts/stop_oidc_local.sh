#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${1:-${ROOT_DIR}/.env.oidc-local}}"

cd "${ROOT_DIR}"
docker compose -f docker-compose.yml -f docker-compose.oidc-local.yml --env-file "${ENV_FILE}" --profile oidc down --remove-orphans
