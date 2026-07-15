# Blueprint Render - Frontend-Only Demo

## Objetivo

Descrever o blueprint dedicado para publicar apenas o frontend no Render, sem backend real e sem preenchimento manual de segredos.

O arquivo canônico deste recorte fica em [render.frontend-only.yaml](../render.frontend-only.yaml).

## Papel Canonico

Use este documento para:

- publicar uma vitrine visual do frontend no Render
- validar build, assets, tema, i18n e shell principal sem depender de APIs reais
- subir um deploy sem `sync: false`, sem `auth-service`, sem `Keycloak` e sem banco

Nao use este documento para:

- validar login real
- validar OIDC, MFA, RBAC, APIs, workers ou observabilidade
- substituir o blueprint full-stack em [render-staging-blueprint.md](./render-staging-blueprint.md)

## Decisao Arquitetural

Este recorte existe como opcao mais barata e menos arriscada quando a prioridade e:

- publicar o frontend rapidamente
- evitar segredos no painel do Render
- demonstrar identidade visual e navegacao de alto nivel

Trade-offs aceitos:

- o login fica desativado
- os modulos aparecem como vitrine, nao como cockpit operacional
- nao existe garantia funcional dos fluxos regulatórios
- o deploy nao prova readiness tecnica nem regulatoria

## Topologia

- `ontrackchain-frontend-demo-staging`: `web` publico
- sem `gateway`
- sem `auth-service`
- sem `Keycloak`
- sem APIs privadas
- sem banco

## Contrato do Runtime

- `APP_ENV=staging`
- `AUTH_MODE=oidc`
- `DEV_AUTH_ENABLED=false`
- `NEXT_PUBLIC_APP_ENV=staging`
- `NEXT_PUBLIC_AUTH_MODE=oidc`
- `NEXT_PUBLIC_DEV_AUTH_ENABLED=false`
- `NEXT_PUBLIC_FRONTEND_STANDALONE_DEMO_MODE=true`
- `NEXT_PUBLIC_FRONTEND_URL=https://ontrackchain-frontend-demo-staging.onrender.com`
- `NEXT_PUBLIC_APP_URL=https://ontrackchain-frontend-demo-staging.onrender.com`
- `healthCheckPath=/api/healthz`

## Comportamento Esperado

- `/api/healthz` responde sem depender de envs internas do stack full-stack
- a home sobe em modo demonstrativo
- o menu lateral e os links operacionais ficam bloqueados cedo para evitar navegação para superfícies que exigem backend
- a página de login informa explicitamente que o deploy e um `frontend-only demo`

## Fluxo Recomendado

1. abrir o blueprint [render.frontend-only.yaml](../render.frontend-only.yaml)
2. criar o serviço `ontrackchain-frontend-demo-staging`
3. executar o `sync` sem preencher segredos
4. validar `https://ontrackchain-frontend-demo-staging.onrender.com/api/healthz`
5. validar `https://ontrackchain-frontend-demo-staging.onrender.com/`
6. confirmar que `/login` exibe o aviso de demo e nao tenta autenticar

## Gate de Saida

Considere este recorte pronto apenas se:

- o deploy convergir sem preenchimento manual
- `/api/healthz` responder `200`
- a home carregar sem erro de runtime
- o login exibir a degradacao esperada de `frontend-only demo`

## Relacao com o Blueprint Full-Stack

- `render.frontend-only.yaml` serve para vitrine sem segredos
- `render.yaml` continua sendo a fonte canônica para staging real do produto
- nao promova este recorte como se fosse prova de integracao, seguranca ou readiness
