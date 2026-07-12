#!/bin/sh
set -eu

python3 /opt/keycloak/bin/render_realm.py

exec /opt/keycloak/bin/kc.sh start-dev \
  --import-realm \
  --proxy-headers=xforwarded \
  --hostname="${KEYCLOAK_PUBLIC_URL}" \
  --hostname-strict=false
