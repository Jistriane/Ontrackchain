#!/bin/sh
set -eu

if [ -z "${PROMETHEUS_HOSTPORT:-}" ]; then
  echo "missing required env: PROMETHEUS_HOSTPORT" >&2
  exit 1
fi

config_file=/etc/grafana/provisioning/datasources/datasource.yml
cp /etc/grafana/provisioning/datasources/datasource.template.yml "$config_file"

escaped_value=$(printf '%s' "${PROMETHEUS_HOSTPORT}" | sed 's/[\/&]/\\&/g')
sed -i "s|\${PROMETHEUS_HOSTPORT}|$escaped_value|g" "$config_file"

exec /run.sh
