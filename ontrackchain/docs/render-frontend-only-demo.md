# Blueprint Render - Frontend Standalone Showcase

## Objetivo

Descrever o blueprint padrao para publicar apenas o frontend no Render, sem backend real, sem login verdadeiro e sem preenchimento manual de segredos.

O arquivo canônico consumido pelo Render para este recorte agora fica em [render.yaml](../render.yaml).
O arquivo [render.frontend-only.yaml](../render.frontend-only.yaml) permanece como alias explicito de compatibilidade.

## Papel Canonico

Use este documento para:

- publicar um `standalone showcase` do frontend no Render
- validar build, assets, tema, i18n, shell principal e navegação completa sem depender de APIs reais
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

- o login real deixa de existir e vira apenas porta de entrada para o showcase
- os modulos aparecem como cockpit visual com dados seeded e interações locais
- nao existe garantia funcional dos fluxos regulatórios
- o deploy nao prova readiness tecnica nem regulatoria

## Topologia

- `ontrackchain-frontend-showcase-staging`: `web` publico
- sem `gateway`
- sem `auth-service`
- sem `Keycloak`
- sem APIs privadas
- sem banco

## Contrato do Runtime

- `APP_ENV=staging`
- `AUTH_MODE=oidc`
- `NEXT_PUBLIC_APP_ENV=staging`
- `NEXT_PUBLIC_AUTH_MODE=oidc`
- `FRONTEND_STANDALONE_SHOWCASE_MODE=true`
- `NEXT_PUBLIC_FRONTEND_STANDALONE_SHOWCASE_MODE=true`
- `NEXT_PUBLIC_FRONTEND_URL=https://ontrackchain-frontend-showcase-staging.onrender.com`
- `NEXT_PUBLIC_APP_URL=https://ontrackchain-frontend-showcase-staging.onrender.com`
- `healthCheckPath=/api/healthz`

## Comportamento Esperado

- `/api/healthz` responde sem depender de envs internas do stack full-stack
- a home sobe em modo `standalone showcase`
- o menu lateral e as rotas do frontend ficam navegáveis
- a página de login informa explicitamente que o deploy nao usa backend real nem autenticação operacional

## Fluxo Recomendado

1. abrir o blueprint [render.yaml](../render.yaml)
2. criar o serviço `ontrackchain-frontend-showcase-staging`
3. executar o `sync` sem preencher segredos
4. validar `https://ontrackchain-frontend-showcase-staging.onrender.com/api/healthz`
5. validar `https://ontrackchain-frontend-showcase-staging.onrender.com/`
6. confirmar que `/login` redireciona o usuário para a experiência de showcase sem autenticação real
7. validar `https://ontrackchain-frontend-showcase-staging.onrender.com/dashboard`
8. confirmar que os atalhos principais do dashboard navegam para `/alerts`, `/monitoring`, `/reports`, `/evidence`, `/billing` e `/team`

## Gate de Saida

Considere este recorte pronto apenas se:

- o deploy convergir sem preenchimento manual
- `/api/healthz` responder `200`
- a home carregar sem erro de runtime
- o shell principal carregar sem depender de backend real
- o dashboard carregar com dados seeded
- os botões principais do dashboard navegarem sem chamar backend privado

## Smoke Recomendado

Executar pelo menos a suíte pública mínima do showcase:

```bash
TEST_SHOWCASE_MODE=true TEST_BASE_URL=http://127.0.0.1:3001 npm run test:e2e -- \
  tests/e2e/showcase-auth.spec.ts \
  tests/e2e/showcase-monitoring.spec.ts \
  tests/e2e/showcase-dashboard.spec.ts \
  tests/e2e/showcase-evidence.spec.ts
```

## Relacao com o Blueprint Full-Stack

- `render.yaml` e o blueprint padrao para vitrine sem segredos
- `render.frontend-only.yaml` permanece como alias explicito deste mesmo recorte
- `render.full-stack.yaml` passa a ser a fonte canônica para staging real do produto
- nao promova este recorte como se fosse prova de integracao, seguranca ou readiness
