FROM grafana/grafana:11.2.0

USER root

RUN rm -f /etc/grafana/provisioning/datasources/datasource.yaml

COPY infra/observability/grafana/provisioning/dashboards /etc/grafana/provisioning/dashboards
COPY infra/observability/grafana/dashboards /var/lib/grafana/dashboards
COPY infra/render/grafana/datasource.template.yml /etc/grafana/provisioning/datasources/datasource.template.yml
COPY infra/render/grafana/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
