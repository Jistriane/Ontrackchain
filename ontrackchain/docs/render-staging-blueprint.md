# Blueprint Render para Staging Full-Stack

## Objetivo

Documentar o blueprint do Render atualmente versionado na raiz tecnica do repositório, agora restaurado como `staging full-stack` minimo viavel para validar:

- `OIDC + MFA` em trilho mais próximo do real
- banco persistente gerenciado
- workers e filas assíncronas
- `ROS/COAF` com `report-api` real
- observabilidade com `Prometheus`, `Alertmanager` e `Grafana`

O arquivo canônico consumido pelo Render continua na raiz técnica deste diretório Git em [render.yaml](../render.yaml).

## Papel Canonico

Este documento e a fonte primaria para:

- topologia hospedada atual do Render em modo `staging full-stack`
- servicos provisionados, bindings e limites assumidos do runtime hospedado
- ordem de preenchimento manual dos segredos `sync: false` no painel
- trade-offs arquiteturais de usar o Render como baseline hospedada de staging

Nao use este documento para:

- substituir o rito tecnico `prepare -> validate -> preflight -> run`: use [Deploy e Staging](./deploy-and-staging.md)
- decidir promocao ou `go/no-go` formal: use [Gates de Release para Staging Serio](./project-release-gates.md)
- configurar o workflow manual e o secret multi-linha do GitHub Actions: use [GitHub Environment para Staging Serio](./github-environment-staging-serious.md)

## Estado Atual

O blueprint vigente volta a provisionar a malha principal de staging:

- `ontrackchain-gateway-staging`: `web` público com `Traefik`
- `ontrackchain-keycloak-staging`: `web` público para o IdP `OIDC`
- `ontrackchain-auth-service-staging`: `web` público para `/auth/config`, `/validate` e bootstrap idempotente do banco
- `ontrackchain-public-api-staging`: `pserv`
- `ontrackchain-investigation-api-staging`: `pserv`
- `ontrackchain-investigation-worker-staging`: `worker`
- `ontrackchain-compliance-api-staging`: `pserv`
- `ontrackchain-compliance-worker-staging`: `worker`
- `ontrackchain-monitoring-api-staging`: `pserv`
- `ontrackchain-report-api-staging`: `pserv`
- `ontrackchain-frontend-staging`: `pserv`
- `ontrackchain-alertmanager-staging`: `pserv`
- `ontrackchain-prometheus-staging`: `pserv`
- `ontrackchain-grafana-staging`: `web` público
- `ontrackchain-redis-staging`: `keyvalue`
- `ontrackchain-postgres-staging`: `Render Postgres` `basic-256mb`

Parâmetros arquiteturais principais:

- `APP_ENV=staging`
- `AUTH_MODE=oidc`
- `DEV_AUTH_ENABLED=false`
- `NEXT_PUBLIC_API_BASE_URL=https://ontrackchain-gateway-staging.onrender.com`
- `KEYCLOAK_PUBLIC_URL=https://ontrackchain-keycloak-staging.onrender.com`
- `JWT_AUDIENCE=ontrackchain-api`
- banco gerenciado referenciado via `fromDatabase`
- Redis/Valkey gerenciado referenciado via `fromService`

## Decisão Arquitetural

Esta opção volta a alinhar o deploy público do Render com a arquitetura real do produto, sem ainda tratar o ambiente como produção.

Trade-off aceito:

- aumenta custo e superfície operacional em relação ao recorte `frontend-only`
- reduz o risco arquitetural de validar a UI fora do contexto de auth, banco, filas e APIs reais
- mantém alguns segredos como `sync: false` para preenchimento manual no painel
- usa URLs públicas `*.onrender.com` como baseline de bootstrap, com possibilidade de override posterior para domínios próprios
- ainda não substitui a homologação formal de produção nem o rito completo de `go/no-go`

## Topologia Atual

[[diagram: staging full-stack no Render com ontrackchain-gateway-staging como único ponto público principal para a aplicação; navegador acessa o gateway Traefik, que roteia para frontend privado Next.js e APIs privadas public-api, investigation-api, compliance-api, monitoring-api e report-api; auth-service público atende /auth/config e /validate e conversa com Postgres gerenciado; ontrackchain-keycloak-staging expõe o IdP OIDC com redirect para o gateway; investigation-worker e compliance-worker processam filas usando Key Value gerenciado; monitoring-api recebe webhook do Alertmanager privado; Prometheus privado coleta métricas de investigation-api, compliance-api, monitoring-api e report-api; Grafana público lê o Prometheus; Postgres gerenciado persiste dados multi-tenant e ROS/COAF.]]

## O Que Este Blueprint Entrega

- gateway público unificando `frontend` e APIs privadas
- `OIDC` com `Keycloak` no próprio Render
- `auth-service` com bootstrap idempotente do schema via `apply_postgres_bootstrap.py`
- `Postgres` persistente no plano `basic-256mb`
- `Key Value` gerenciado para fila/cache compatível com Redis
- `Prometheus`, `Alertmanager` e `Grafana`
- workers reais de `investigation` e `compliance`
- base suficiente para validar `ROS/COAF`, `blocks`, `counterparties`, `work-items` e screening

## O Que Funciona Neste Modo

- login OIDC com `Keycloak` no próprio ambiente
- emissão e validação de sessão com `auth-service`
- SSR do frontend usando gateway real
- fluxos de `reports` e `ROS/COAF` com `report-api` real
- screening, `counterparties`, `blocks` e `work-items` com `compliance-api`
- alertas operacionais e webhook do `Alertmanager` com `monitoring-api`
- observabilidade básica via `Prometheus` e `Grafana`

## O Que Ainda Fica Limitado

- o ambiente continua dependente de preenchimento manual de segredos `OIDC`, `TRM`, `RPC`, `Grafana` e feed UE
- o baseline do blueprint usa subdomínios `onrender.com`, não os domínios corporativos finais
- as senhas seed do realm do `Keycloak` podem ser rotacionadas por variáveis opcionais no painel, mas não fazem parte da baseline pública do repositório
- a janela séria ainda depende de evidência humana, preflight e `go/no-go` formal

## Quando Usar

Use este blueprint quando:

- o objetivo imediato for validar a arquitetura real em `staging`
- for necessário aproximar o ambiente de `produção` sem promover o stack completo final
- `ROS/COAF`, `OIDC`, `alerts`, `work-items` e `evidence` precisarem de backend real
- o time precisar de um alvo consistente para smoke, readiness bundle e homologação incremental

## Quando Não Usar

Não trate este blueprint como staging sério quando o objetivo for:

- pular a etapa de preenchimento manual de segredos
- substituir a validação de `preflight`, smoke e Playwright por “deploy subiu = está pronto”
- tratar `onrender.com` como política final de domínio/segurança
- assumir que `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true` sem homologação real
- declarar `produção` pronta sem artefatos de retention/recovery e `go/no-go`

Para esses cenários, siga o rito de staging completo documentado em [deploy-and-staging.md](./deploy-and-staging.md).

## Segredos e Preenchimento Manual

O blueprint usa `sync: false` para segredos sensiveis, mas eles nao tem o mesmo peso operacional.

Obrigatorios para o primeiro `sync` do runtime hospedado:

- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_B2B_CLIENT_SECRET`
- `KEYCLOAK_ADMIN_CLIENT_SECRET`
- `JWT_HS256_SECRET`
- `MFA_TOTP_SECRET`
- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
- `GRAFANA_ADMIN_PASSWORD`

Obrigatorios para homologacao seria com escopo regulatorio e providers reais:

- `COMPLIANCE_TRM_SCREENING_URL`
- `COMPLIANCE_TRM_API_KEY`
- `OPENSANCTIONS_API_KEY`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`
- `INVESTIGATION_RPC_PRIMARY_URL`
- `INVESTIGATION_RPC_FALLBACK_URL`

Rotação opcional dos usuários seed do realm no painel:

- `KEYCLOAK_SYSTEM_USER_PASSWORD`
- `KEYCLOAK_KMD_TESTER_PASSWORD`
- `KEYCLOAK_JIBSO_ADMIN_PASSWORD`
- `KEYCLOAK_AUDITOR_PASSWORD`
- `KEYCLOAK_ANALYST_PASSWORD`
- `KEYCLOAK_VIEWER_PASSWORD`
- `KEYCLOAK_SEM_ORG_PASSWORD`

## Checklist Manual do Painel do Render

Use esta ordem no painel para reduzir retries improdutivos e evitar que a malha suba com dependencias criticas faltando.

### Etapa 1. Primeiro `sync` do runtime hospedado

Preencha apenas o minimo necessario para a malha principal convergir:

**`ontrackchain-keycloak-staging`**

- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_B2B_CLIENT_SECRET`
- opcional: deixe as senhas seed vazias no primeiro `sync`, a menos que a janela exija rotacao imediata

**`ontrackchain-auth-service-staging`**

- `KEYCLOAK_ADMIN_CLIENT_SECRET`
- `JWT_HS256_SECRET`
- `MFA_TOTP_SECRET`

Parametros nao sensiveis ja declarados no blueprint para o diretório federado:

- `KEYCLOAK_ADMIN_BASE_URL=https://ontrackchain-keycloak-staging.onrender.com`
- `KEYCLOAK_ADMIN_REALM=ontrackchain`
- `KEYCLOAK_ADMIN_CLIENT_ID=ontrackchain-b2b`
- `KEYCLOAK_ADMIN_TIMEOUT_SECONDS=5`
- `KEYCLOAK_ADMIN_SEARCH_LIMIT=20`
- `KEYCLOAK_ADMIN_ORG_ATTRIBUTE=organization_id`
- `KEYCLOAK_ADMIN_ROLE_ATTRIBUTE=otk_role`

Observacao operacional deste corte:

- enquanto nao existir um client read-only dedicado para a Admin API, `KEYCLOAK_ADMIN_CLIENT_SECRET` pode espelhar o mesmo valor de `KEYCLOAK_B2B_CLIENT_SECRET`, desde que o client `ontrackchain-b2b` receba escopo minimo suficiente apenas para leitura do diretório

**`ontrackchain-monitoring-api-staging`**

- `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`

**`ontrackchain-grafana-staging`**

- `GRAFANA_ADMIN_PASSWORD`

Nao ha preenchimento manual inicial para:

- `ontrackchain-gateway-staging`
- `ontrackchain-public-api-staging`
- `ontrackchain-frontend-staging`
- `ontrackchain-prometheus-staging`
- `ontrackchain-alertmanager-staging` quando o token vier de `ontrackchain-monitoring-api-staging` via `fromService`
- `ontrackchain-postgres-staging` e `ontrackchain-redis-staging` no eixo de `sync: false`, porque o blueprint usa propriedades gerenciadas do Render

### Etapa 2. Segredos de providers reais

Preencha somente quando a janela incluir homologacao seria ou prova regulatoria com integracoes externas:

**`ontrackchain-investigation-api-staging`**

- `INVESTIGATION_RPC_PRIMARY_URL` quando `ONTRACKCHAIN_EXPECT_RPC_MODE=live`
- `INVESTIGATION_RPC_FALLBACK_URL`

**`ontrackchain-investigation-worker-staging`**

- `INVESTIGATION_RPC_PRIMARY_URL` quando `ONTRACKCHAIN_EXPECT_RPC_MODE=live`
- `INVESTIGATION_RPC_FALLBACK_URL`

**`ontrackchain-compliance-api-staging`**

- `COMPLIANCE_TRM_SCREENING_URL`
- `COMPLIANCE_TRM_API_KEY`

**`ontrackchain-compliance-worker-staging`**

- `OPENSANCTIONS_API_KEY`
- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`

Regras operacionais desta etapa:

- se a janela estiver em `fallback_only`, mantenha `INVESTIGATION_RPC_PRIMARY_URL` vazio e replique apenas `INVESTIGATION_RPC_FALLBACK_URL` no `investigation-api` e no `investigation-worker`
- se a janela estiver em `live`, replique exatamente os mesmos valores de `RPC` no `investigation-api` e no `investigation-worker`
- nao marque a trilha `AML/KYT live` como pronta sem preencher `COMPLIANCE_TRM_SCREENING_URL` e `COMPLIANCE_TRM_API_KEY`
- trate `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` como obrigatoria apenas quando o escopo incluir o feed UE real
- trate `OPENSANCTIONS_API_KEY` como obrigatoria quando o worker de sancoes enriquecido fizer parte do escopo serio

### Etapa 3. Verificacao imediata apos salvar

Depois de preencher cada grupo, valide no painel e no runtime:

- o servico aceitou a alteracao sem erro de validacao
- o deploy foi reacionado para o servico correto
- o health check do servico voltou a verde
- o valor salvo nao ficou vazio ou com placeholder

## Fluxo Recomendado

1. subir o blueprint a partir de `render.yaml` na raiz tecnica do repositório;
2. preencher no painel do Render os segredos obrigatorios do primeiro `sync`;
3. aguardar a convergencia inicial do `gateway`, `Keycloak`, `auth-service`, `frontend`, `Postgres`, `Key Value`, `Prometheus`, `Alertmanager` e `Grafana`;
4. validar `https://ontrackchain-gateway-staging.onrender.com/login`;
5. validar `https://ontrackchain-auth-service-staging.onrender.com/health`;
6. validar `https://ontrackchain-keycloak-staging.onrender.com/realms/ontrackchain`;
7. validar `https://ontrackchain-grafana-staging.onrender.com/login`;
8. preencher os segredos de providers reais quando a janela incluir `AML/KYT`, feed UE, OpenSanctions e RPC;
9. executar o rito técnico em [deploy-and-staging.md](./deploy-and-staging.md);
10. usar `ROS/COAF` e os bundles sérios como trilhas principais de prova do ambiente.

Checklist minimo do primeiro `sync`:

- `gateway` responde em `/login`
- `auth-service` responde em `/health`
- `Keycloak` responde no realm `ontrackchain`
- `Grafana` responde em `/api/health`
- `frontend` carrega com `AUTH_MODE=oidc`
- `ROS/COAF` ainda nao e usado como aceite final antes de preencher os segredos de providers e validar identidade persistida

## Roteiro Curto do Operador

Use este bloco durante a execucao real no painel do Render.

### Antes de clicar em `Sync`

1. abrir o blueprint da raiz técnica do repositório e confirmar que o arquivo usado e [render.yaml](../render.yaml)
2. confirmar que o objetivo desta rodada e apenas o primeiro `sync` do runtime hospedado
3. separar previamente os 7 segredos minimos:
   - `KEYCLOAK_ADMIN_PASSWORD`
   - `KEYCLOAK_B2B_CLIENT_SECRET`
   - `KEYCLOAK_ADMIN_CLIENT_SECRET`
   - `JWT_HS256_SECRET`
   - `MFA_TOTP_SECRET`
   - `ALERTMANAGER_WEBHOOK_BEARER_TOKEN`
   - `GRAFANA_ADMIN_PASSWORD`
4. nao abrir a etapa de providers reais nesta rodada

### Execucao no Painel

1. iniciar o `sync` do blueprint
2. preencher `ontrackchain-keycloak-staging`
3. preencher `ontrackchain-auth-service-staging`
4. preencher `ontrackchain-monitoring-api-staging`
5. preencher `ontrackchain-grafana-staging`
6. salvar e deixar o Render reacionar os deploys
7. nao preencher `RPC`, `TRM`, `OpenSanctions` ou feed UE nesta primeira passada

### Critério de `Stop`

Pare imediatamente e nao avance para providers reais se qualquer um destes ocorrer:

- erro de validacao do blueprint
- servico em `deploy failed`
- `gateway` nao responder em `/login`
- `auth-service` nao responder em `/health`
- `Keycloak` nao responder no realm
- `Grafana` nao responder em `/api/health`

Quando parar:

1. registrar qual servico falhou
2. registrar qual segredo foi o ultimo alterado
3. nao preencher novos segredos ate a causa estar clara

### Critério de `Go`

Siga para a etapa de validacao remota somente quando:

- `gateway`, `auth-service`, `Keycloak`, `Grafana` e `frontend` estiverem convergidos
- nao houver erro vermelho no painel do Render para a malha principal
- o ambiente estiver claramente em `AUTH_MODE=oidc`

### Proxima Acao Depois do `Go`

Com a malha principal verde:

1. validar `/login`
2. validar `/health`
3. validar o realm do `Keycloak`
4. validar `Grafana`
5. só entao seguir para o rito em [deploy-and-staging.md](./deploy-and-staging.md)

### Rollback Imediato de Operador

Use rollback imediato apenas como contenção operacional, nao como substituto de diagnostico:

1. remover o ultimo segredo preenchido incorretamente
2. reaplicar o valor correto
3. reexecutar apenas o servico afetado quando o painel permitir
4. se a falha for estrutural do blueprint, interromper a rodada e voltar para revisao documental antes de novo `sync`
