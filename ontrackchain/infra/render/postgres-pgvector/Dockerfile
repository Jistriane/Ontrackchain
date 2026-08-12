FROM pgvector/pgvector:0.7.4-pg16

ENV PGDATA=/var/lib/postgresql/data/pgdata

RUN mkdir -p /var/lib/postgresql/data \
    && chown -R postgres:postgres /var/lib/postgresql/data

COPY --chown=postgres:postgres infra/render/postgres-pgvector/docker-entrypoint-initdb.d/ /docker-entrypoint-initdb.d/

EXPOSE 5432

CMD ["postgres"]
