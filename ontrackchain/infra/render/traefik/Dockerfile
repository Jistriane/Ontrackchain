FROM traefik:v3.1 AS traefik-bin

FROM alpine:3.20

RUN apk add --no-cache ca-certificates

COPY --from=traefik-bin /usr/local/bin/traefik /usr/local/bin/traefik
COPY infra/render/traefik/traefik.yml /etc/traefik/traefik.yml
COPY infra/render/traefik/dynamic.template.yml /etc/traefik/dynamic.template.yml
COPY infra/render/scripts/traefik-entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

EXPOSE 10000

ENTRYPOINT ["/entrypoint.sh"]
