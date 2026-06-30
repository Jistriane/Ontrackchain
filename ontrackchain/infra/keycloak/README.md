# Keycloak Local Scaffold

## Objetivo

Fornecer um scaffold executavel do `Keycloak` para o `WP-01`, com:

- import automatico do realm `ontrackchain`
- clients `ontrackchain-web`, `ontrackchain-api` e `ontrackchain-b2b`
- claims `org`, `plan` e `otk_role`
- usuarios base para validacao inicial do fluxo OIDC

## Decisao Operacional

Este scaffold local usa `KC_DB=dev-file` por design.

Motivo:

- evita acoplar o IdP ao `postgres` principal da plataforma neste primeiro corte
- reduz risco de drift sobre o banco operacional ja inicializado pelo `init.sql`
- mantem o foco do `WP-01` em fluxo de identidade e nao em migracao de infraestrutura

Para ambientes serios, o passo seguinte recomendado e migrar o `Keycloak` para `PostgreSQL` dedicado.

## Como Subir

```bash
COMPOSE_PROFILES=oidc docker compose up -d keycloak
```

## Enderecos Locais

- admin/debug direto: `http://localhost:8088`
- issuer local esperado pelo app: `http://auth.localhost:8080/realms/ontrackchain`

Observacao:

- o host `auth.localhost` e a rota preferida para o fluxo OIDC atras do `Traefik`
- se `auth.localhost` nao resolver no seu ambiente, adicione uma entrada local para `127.0.0.1`

## Credenciais Iniciais

### Admin Console

- usuario: `admin`
- senha: `admin`

### Usuarios do Realm

- `system@ontrackchain.com` / `SystemPass123!`
- `kmd@ontrackchain.com` / `KmdPass123!`
- `jibso@ontrackchain.com` / `JIBSOPass123!`
- `auditor@ontrackchain.com` / `AuditorPass123!`
- `analyst@ontrackchain.com` / `AnalystPass123!`
- `viewer@ontrackchain.com` / `ViewerPass123!`
- `sem-org@ontrackchain.com` / `SemOrgPass123!`

Observacao importante:

- `sem-org@ontrackchain.com` e um usuario de teste intencionalmente mal provisionado
- ele nao possui `organization_id`, portanto deve falhar em `/validate` com `invalid_claims`
- esse usuario existe para validar o caminho negativo do `WP-01` e nao deve ser usado como baseline de smoke positivo

## Reimport do Realm Local

Como este scaffold usa `KC_DB=dev-file`, alterar `realm-ontrackchain.json` nao atualiza um container ja provisionado.

Quando houver mudanca de usuarios, claims ou clients:

```bash
docker compose --profile oidc stop keycloak
docker compose --profile oidc rm -f keycloak
docker volume rm ontrackchain_keycloak_data
docker compose --profile oidc up -d --build keycloak
```

Depois, se necessario, recrie tambem os serviços que consomem o OIDC local:

```bash
docker compose up -d --build auth-service frontend
```

## Variaveis Relevantes

- `KEYCLOAK_PUBLIC_URL`
- `KEYCLOAK_HOSTNAME`
- `KEYCLOAK_HTTP_PORT`
- `KEYCLOAK_ADMIN`
- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_REALM`
- `KEYCLOAK_B2B_CLIENT_SECRET`

## Para Ativar OIDC no App Local

Ajuste o `.env` com:

```env
AUTH_MODE=oidc
DEV_AUTH_ENABLED=false
NEXT_PUBLIC_AUTH_MODE=oidc
NEXT_PUBLIC_DEV_AUTH_ENABLED=false
OIDC_ISSUER_URL=http://auth.localhost:8080/realms/ontrackchain
OIDC_JWKS_URL=http://auth.localhost:8080/realms/ontrackchain/protocol/openid-connect/certs
OIDC_AUTHORIZATION_URL=http://auth.localhost:8080/realms/ontrackchain/protocol/openid-connect/auth
OIDC_AUDIENCE=ontrackchain-api
OIDC_CLIENT_ID=ontrackchain-web
OIDC_ORG_CLAIM=org
OIDC_PLAN_CLAIM=plan
OIDC_ROLE_CLAIM=otk_role
```

Depois, suba o stack normalmente:

```bash
COMPOSE_PROFILES=oidc docker compose up -d
```

## Limites Conhecidos deste Corte

- o claim `otk_role` e emitido pelo scaffold local via atributo do usuario para manter o token deterministico
- as `realm roles` tambem sao provisionadas e atribuidas aos usuarios, mas o mapeamento filtrado de roles pode ser refinado depois com payload real do `Keycloak`
- o client `ontrackchain-api` esta preparado para validacao de `audience`, sem fluxo server-side adicional neste corte
