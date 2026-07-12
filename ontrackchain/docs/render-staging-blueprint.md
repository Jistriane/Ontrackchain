# Render Blueprint para Frontend-Only

## Objetivo

Documentar o blueprint do Render atualmente versionado na raiz do repositório, reduzido para `frontend-only` enquanto as credenciais reais de OIDC, RPC, TRM, OpenSanctions e observabilidade não estiverem disponíveis.

O arquivo canônico consumido pelo Render continua na raiz do repositório Git em [render.yaml](file:///home/jistriane/Ontrackchain/render.yaml).

## Estado Atual

O blueprint vigente provisiona apenas um serviço:

- `ontrackchain-frontend-staging`: serviço `web` do frontend `Next.js`

Parâmetros principais do deploy atual:

- `APP_ENV=test`
- `AUTH_MODE=dev`
- `DEV_AUTH_ENABLED=true`
- `NEXT_PUBLIC_AUTH_MODE=dev`
- `NEXT_PUBLIC_API_BASE_URL=https://ontrackchain-frontend-staging.onrender.com`
- `INTERNAL_API_BASE_URL=https://ontrackchain-frontend-staging.onrender.com`

## Decisão Arquitetural

Esta opção existe para colocar a interface no ar sem bloquear o deploy por falta de segredos externos. Ela não substitui a arquitetura alvo full-stack do produto, mas sim materializa um recorte operacional temporário de menor risco.

Trade-off aceito:

- reduz custo e dependência de terceiros
- elimina a necessidade imediata de Postgres, Redis, Keycloak, APIs privadas e observabilidade no Render
- permite validar shell, layout, assets, rotas públicas e estabilidade básica do frontend
- não entrega staging funcional completo para autenticação real, dados dinâmicos ou fluxos regulatórios fim a fim

## Topologia Atual

[[diagram: deploy frontend-only no Render com um único web service ontrackchain-frontend-staging servindo a aplicação Next.js; navegador acessa a interface pública; não há gateway Traefik, Keycloak, APIs privadas, banco gerenciado, Redis, workers nem observabilidade no blueprint atual; chamadas server-side do frontend apontam para a própria URL pública apenas para manter o bootstrap do shell sem segredos externos.]]

## O Que Foi Removido do Blueprint

O blueprint atual não provisiona:

- `auth-service`
- `public-api`
- `investigation-api` e `investigation-worker`
- `compliance-api` e `compliance-worker`
- `monitoring-api`
- `report-api`
- `Keycloak`
- `Postgres`
- `Redis`
- `Prometheus`, `Alertmanager` e `Grafana`

## O Que Funciona Neste Modo

- carregamento do frontend
- página inicial
- rota `/login`
- assets estáticos
- validação visual e smoke básico do shell

## O Que Fica Limitado

- login real via OIDC
- emissão de sessão com backend real
- dashboards com dados dinâmicos
- fluxos de investigação, compliance, monitoring, reports e evidence dependentes de APIs reais
- bundles sérios de readiness e smoke regulatório fim a fim

## Quando Usar

Use este blueprint quando:

- o objetivo imediato for publicar a UI rapidamente
- as integrações externas ainda não estiverem homologadas
- os segredos reais ainda não estiverem disponíveis
- o time precisar de uma URL pública do frontend para revisão visual, UX ou demonstração controlada

## Quando Não Usar

Não trate este blueprint como staging sério quando o objetivo for:

- validar OIDC real
- rodar smoke de autenticação federada
- validar providers AML/KYT ou feed UE
- testar filas, workers, persistência ou observabilidade
- promover readiness regulatório ou decisão formal de `go/no-go`

Para esses cenários, siga o rito de staging completo documentado em [deploy-and-staging.md](file:///home/jistriane/Ontrackchain/ontrackchain/docs/deploy-and-staging.md).

## Fluxo Recomendado

1. subir o blueprint a partir de `render.yaml` na raiz do repositório;
2. validar `https://ontrackchain-frontend-staging.onrender.com/`;
3. validar `https://ontrackchain-frontend-staging.onrender.com/login`;
4. confirmar ausência de crash de runtime no shell;
5. usar este ambiente apenas como preview operacional do frontend até a volta do stack completo.
