FROM quay.io/keycloak/keycloak:25.0.6

USER root

COPY infra/keycloak/realm-ontrackchain.json /opt/keycloak/data/import/realm-ontrackchain.base.json
COPY infra/keycloak/realm-ontrackchain.json /opt/keycloak/data/import/realm-ontrackchain.json
COPY infra/render/keycloak/render_realm.py /opt/keycloak/bin/render_realm.py
COPY infra/render/keycloak/entrypoint.sh /opt/keycloak/bin/ontrackchain-render-entrypoint.sh

RUN chmod +x /opt/keycloak/bin/ontrackchain-render-entrypoint.sh \
  && mkdir -p /opt/keycloak/data/import \
  && chmod -R 777 /opt/keycloak/data/import

USER keycloak

ENTRYPOINT ["/opt/keycloak/bin/ontrackchain-render-entrypoint.sh"]
