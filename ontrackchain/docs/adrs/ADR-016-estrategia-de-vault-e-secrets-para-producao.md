# ADR-016 — Estrategia de Vault e Secrets para Producao

## Contexto

O projeto atualmente gerencia segredos via:
- `.env` para desenvolvimento local
- `.env.staging.private` para staging (via GitHub Environment)
- variaveis de ambiente no Render para producao

Essa abordagem apresenta riscos:
- segredos em texto plain text em arquivos `.env`
- sem rotacao automatica de credenciais
- sem audit trail de acesso a segredos
- sem segregacao de ambientes em producao

Para ambiente regulado, e necessario:
- secret manager com controle de acesso
- rotacao automatica de credenciais
- audit trail de leitura/escrita de segredos
- segregacao clara entre ambientes

## Decisao

Adotar estrategia de secrets em duas camadas:

### 1. Producao — Secret Manager

Usar servico de secret manager (AWS Secrets Manager, HashiCorp Vault, ou equivalente):
- todos os segredos criticos devem ser armazenados no secret manager
- rotacao automatica para credenciais de banco, APIs e servicos
- audit trail de acesso
- integração com IAM para controle de acesso

### 2. Staging — GitHub Environment (manter)

Manter o modelo atual de GitHub Environment para staging:
- `.env.staging.private` continua sendo a fonte de verdade para staging
- GitHub Environment fornece approval gates e audit trail
- staging nao exige secret manager dedicado

### 3. Desenvolvimento — .env (manter)

Manter o modelo atual de `.env` para desenvolvimento:
- valores nao-produtivos
- controle de versao no repositorio (exceto `.env` real)
- facilita onboarding de desenvolvedores

## Mapeamento de Segredos

| Segredo | Producao | Staging | Desenvolvimento |
|---------|----------|---------|-----------------|
| `POSTGRES_PASSWORD` | Secret Manager | .env.staging.private | .env |
| `JWT_HS256_SECRET` | Secret Manager | .env.staging.private | .env |
| `OIDC_CLIENT_SECRET` | Secret Manager | .env.staging.private | .env |
| `TRM_API_KEY` | Secret Manager | .env.staging.private | .env |
| `GRAFANA_ADMIN_PASSWORD` | Secret Manager | .env.staging.private | .env |
| `KEYCLOAK_ADMIN_PASSWORD` | Secret Manager | .env.staging.private | .env |

## Nomenclatura de Segredos

```
ontrackchain/<ambiente>/<servico>/<nome_segredo>
```

Exemplos:
- `ontrackchain/production/auth/jwt_hs256_secret`
- `ontrackchain/production/postgres/password`
- `ontrackchain/production/compliance/trm_api_key`
- `ontrackchain/staging/auth/jwt_hs256_secret`

## Consequencias

- melhora significativa na segurança de producao
- audit trail de acesso a segredos
- rotacao automatica reduz risco de credenciais comprometidas
- segregacao clara entre ambientes
- maior complexidade operacional inicial

## Trade-offs Aceitos

- custo adicional de secret manager em producao
- necessidade de integração com CI/CD para leitura de segredos
- periodo de transicao com coexistencia de modelos

## Status

- Aceito para implementacao faseada
- Fase 1: documentar mapeamento atual de segredos
- Fase 2: implementar secret manager em producao
- Fase 3: migrar staging para dual-mode (GitHub Environment + secret manager)
