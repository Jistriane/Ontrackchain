#!/bin/sh
set -eu

required_envs="
MONITORING_API_HOSTPORT
ALERTMANAGER_WEBHOOK_BEARER_TOKEN
"

for name in $required_envs; do
  eval "value=\${$name:-}"
  if [ -z "$value" ]; then
    echo "missing required env: $name" >&2
    exit 1
  fi
done

config_file=/etc/alertmanager/alertmanager.yml
cp /etc/alertmanager/alertmanager.template.yml "$config_file"

for name in $required_envs; do
  eval "value=\${$name}"
  escaped_value=$(printf '%s' "$value" | sed 's/[\/&]/\\&/g')
  sed -i "s|\${$name}|$escaped_value|g" "$config_file"
done

exec /bin/alertmanager --config.file=/etc/alertmanager/alertmanager.yml
