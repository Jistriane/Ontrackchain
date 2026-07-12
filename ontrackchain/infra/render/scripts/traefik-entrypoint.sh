#!/bin/sh
set -eu

required_envs="
AUTH_SERVICE_HOSTPORT
PUBLIC_API_HOSTPORT
INVESTIGATION_API_HOSTPORT
COMPLIANCE_API_HOSTPORT
MONITORING_API_HOSTPORT
REPORT_API_HOSTPORT
FRONTEND_HOSTPORT
"

for name in $required_envs; do
  eval "value=\${$name:-}"
  if [ -z "$value" ]; then
    echo "missing required env: $name" >&2
    exit 1
  fi
done

dynamic_file=/etc/traefik/dynamic.yml
cp /etc/traefik/dynamic.template.yml "$dynamic_file"

for name in $required_envs; do
  eval "value=\${$name}"
  escaped_value=$(printf '%s' "$value" | sed 's/[\/&]/\\&/g')
  sed -i "s|\${$name}|$escaped_value|g" "$dynamic_file"
done

exec /usr/local/bin/traefik --configFile=/etc/traefik/traefik.yml
