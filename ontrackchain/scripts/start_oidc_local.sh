#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${1:-${ROOT_DIR}/.env.oidc-local}}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[oidc-local] env file ausente: ${ENV_FILE}" >&2
  echo "[oidc-local] copie ${ROOT_DIR}/.env.oidc-local.example para ${ROOT_DIR}/.env.oidc-local e ajuste os valores locais" >&2
  exit 1
fi

cd "${ROOT_DIR}"

docker compose -f docker-compose.yml -f docker-compose.oidc-local.yml --env-file "${ENV_FILE}" --profile oidc up -d --build --force-recreate \
  traefik postgres redis keycloak auth-service public-api investigation-api investigation-worker compliance-api compliance-worker monitoring-api report-api frontend
