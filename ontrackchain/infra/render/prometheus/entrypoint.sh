#!/bin/sh
set -eu

required_envs="
ALERTMANAGER_HOSTPORT
INVESTIGATION_API_HOSTPORT
MONITORING_API_HOSTPORT
COMPLIANCE_API_HOSTPORT
REPORT_API_HOSTPORT
"

for name in $required_envs; do
  eval "value=\${$name:-}"
  if [ -z "$value" ]; then
    echo "missing required env: $name" >&2
    exit 1
  fi
done

config_file=/etc/prometheus/prometheus.yml
cp /etc/prometheus/prometheus.template.yml "$config_file"

for name in $required_envs; do
  eval "value=\${$name}"
  escaped_value=$(printf '%s' "$value" | sed 's/[\/&]/\\&/g')
  sed -i "s|\${$name}|$escaped_value|g" "$config_file"
done

exec /bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.enable-lifecycle
