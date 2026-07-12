FROM prom/alertmanager:v0.28.1

USER root

COPY infra/render/alertmanager/alertmanager.template.yml /etc/alertmanager/alertmanager.template.yml
COPY infra/render/alertmanager/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

USER nobody

ENTRYPOINT ["/entrypoint.sh"]
