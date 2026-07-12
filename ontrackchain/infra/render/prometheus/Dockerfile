FROM prom/prometheus:v2.55.1

USER root

COPY infra/observability/investigation.rules.yml /etc/prometheus/rules/investigation.rules.yml
COPY infra/observability/monitoring.rules.yml /etc/prometheus/rules/monitoring.rules.yml
COPY infra/observability/compliance.rules.yml /etc/prometheus/rules/compliance.rules.yml
COPY infra/observability/report.rules.yml /etc/prometheus/rules/report.rules.yml
COPY infra/observability/platform.rules.yml /etc/prometheus/rules/platform.rules.yml
COPY infra/render/prometheus/prometheus.template.yml /etc/prometheus/prometheus.template.yml
COPY infra/render/prometheus/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

USER nobody

ENTRYPOINT ["/entrypoint.sh"]
