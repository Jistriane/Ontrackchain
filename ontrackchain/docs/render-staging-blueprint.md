# Render Blueprint para Staging

## Objetivo

Definir um blueprint unico para staging no Render sem quebrar a arquitetura atual baseada em gateway path-based.

## Decisoes Arquiteturais

- `ontrackchain-staging` e o unico entrypoint publico da aplicacao.
- `frontend`, `auth-service`, APIs e observabilidade ficam na private network do Render.
- `ontrackchain-auth-idp-staging` permanece publico porque o fluxo OIDC precisa de um issuer acessivel pelo navegador.
- o `frontend` continua consumindo um `INTERNAL_API_BASE_URL` unico, agora fornecido pelo gateway interno do Render.
- o bootstrap do Postgres sai do `docker-entrypoint-initdb.d` e passa para `preDeployCommand` do `auth-service`, usando lock advisory para manter idempotencia.

## Topologia

[[diagram: staging Render com gateway publico ontrackchain-staging roteando / para frontend privado, /auth para auth-service privado, /public para public-api privado e /api/v1/* para APIs privadas; Keycloak publico separado em ontrackchain-auth-idp-staging; Postgres gerenciado e Redis gerenciado consumidos por auth-service, investigation-api/worker, compliance-api/worker, monitoring-api e report-api; Prometheus, Alertmanager e Grafana privados conectados aos hostports internos dos servicos.]]

## Servicos do Blueprint

- `ontrackchain-staging`: gateway Traefik publico.
- `ontrackchain-auth-idp-staging`: Keycloak publico para OIDC.
- `ontrackchain-frontend-staging`: Next.js privado.
- `ontrackchain-auth-staging`: auth-service privado com bootstrap de banco.
- `ontrackchain-public-api-staging`: public-api privado exposto via gateway em `/public`.
- `ontrackchain-investigation-api-staging` e `ontrackchain-investigation-worker-staging`.
- `ontrackchain-compliance-api-staging` e `ontrackchain-compliance-worker-staging`.
- `ontrackchain-monitoring-api-staging`.
- `ontrackchain-report-api-staging`.
- `ontrackchain-prometheus-staging`, `ontrackchain-alertmanager-staging` e `ontrackchain-grafana-staging`.
- `ontrackchain-postgres-staging` e `ontrackchain-redis-staging`.

## Variaveis Criticas

- preencha todos os `sync: false` no Render antes do primeiro deploy.
- use `infra/render/render-staging.example.env` como checklist de secrets, nao como arquivo para commit.
- use [Primeiro Sync no Render](file:///home/jistriane/Ontrackchain/ontrackchain/docs/render-staging-first-sync.md) como runbook operacional para a ordem de preenchimento e validacao inicial.
- se o Render gerar subdominios diferentes dos nomes previstos, atualize:
  - `ONTRACKCHAIN_PUBLIC_BASE_URL`
  - `KEYCLOAK_PUBLIC_URL`
  - `OIDC_ISSUER_URL`
  - `OIDC_JWKS_URL`
  - `OIDC_AUTHORIZATION_URL`
  - `NEXT_PUBLIC_API_BASE_URL`

## Bootstrap do Banco

- o script `infra/render/scripts/apply_postgres_bootstrap.py` aplica `init.sql` apenas quando a base esta vazia.
- depois aplica todas as migrations `.sql` em ordem alfabetica.
- o estado fica registrado em `render_schema_migrations`.
- o lock `pg_advisory_lock` evita corrida entre deploys concorrentes.

## Riscos e Trade-offs

- custo: o blueprint provisiona muitos servicos `starter`; e o caminho de menor risco para preservar a arquitetura atual, mas nao o mais barato.
- Keycloak: continua em `KC_DB=dev-file` para reduzir escopo do primeiro staging; para maior resiliência, o proximo passo e migrar o IdP para Postgres dedicado.
- observabilidade: Prometheus e Grafana entram como servicos privados; se houver necessidade de acesso humano remoto, adicione um gateway administrativo com allowlist.
- subdominio: o blueprint assume os `*.onrender.com` derivados dos nomes definidos; valide isso no primeiro sync.

## Fluxo Recomendado

1. subir o blueprint a partir de `render.yaml`;
2. preencher todos os `sync: false`;
3. validar `ontrackchain-auth-idp-staging` e `ontrackchain-staging`;
4. executar smoke OIDC e E2E criticos;
5. revisar custo e estabilidade antes de promover qualquer endurecimento adicional.
