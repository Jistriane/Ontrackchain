#!/bin/sh
set -eu

if command -v python3 >/dev/null 2>&1; then
  python3 /opt/keycloak/bin/render_realm.py
elif [ ! -f /opt/keycloak/data/import/realm-ontrackchain.json ]; then
  cp /opt/keycloak/data/import/realm-ontrackchain.base.json /opt/keycloak/data/import/realm-ontrackchain.json
fi

exec /opt/keycloak/bin/kc.sh start-dev \
  --import-realm \
  --proxy-headers=xforwarded \
  --hostname="${KEYCLOAK_PUBLIC_URL}" \
  --hostname-strict=false
