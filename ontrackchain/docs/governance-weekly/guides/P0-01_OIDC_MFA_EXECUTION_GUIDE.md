# Guia de Execucao Assistida - `P0-01` OIDC + MFA serio

## Objetivo

Concentrar em um unico artefato o rito minimo para mover `P0-01` de `blocked` para `in_progress`, executar a validacao de `OIDC + MFA` em ambiente serio com evidencia preservada e devolver a trilha para a governanca semanal sem drift.

## Quando Usar

- quando os secrets reais de `OIDC` e `MFA` ja estiverem disponiveis fora do repositorio
- quando houver owner nominal confirmado para `Auth/OIDC`
- quando a janela seria incluir `P0-01` isolado ou combinado com `P0-02/P0-03`

## Fontes Canonicas

- [Deploy e Staging](../../deploy-and-staging.md)
- [Checklist de Evidência Mínima da Primeira Janela Séria](../../history/first-serious-window-evidence-checklist.md)
- [Project Release Gates](../../project-release-gates.md)
- [Project Operational Execution Board](../../project-operational-execution-board.md)
- [Staging Env Ownership](../../staging-env-ownership.md)

## Artefato Complementar

- [Run Sheet Operacional de `P0-01` OIDC + MFA serio](./P0-01_OIDC_MFA_RUN_SHEET.md)

## Estado Inicial Esperado

- `P0-01` ainda esta em `blocked`
- o baseline local nao prova `OIDC + MFA` serio sem override real de ambiente
- `MFA_EXTERNAL_PROVIDER_HOMOLOGATED` pode seguir `false` ate existir homologacao externa real
- a janela nao pode promover maturidade sem `preflight`, `smoke`, bundle OIDC e evidência revisavel

## Requisitos Minimos

### Owner e Handoff

- grupo: `Auth/OIDC`
- owner esperado: `Backend/Auth`
- apoio: `Platform/SRE`
- atualizar somente `date` e `status` em `docs/staging-env-ownership.md`

### Segredos Obrigatorios

Preencher apenas em `.env.staging.private` local ou no ambiente serio equivalente:

- `JWT_HS256_SECRET`
- `MFA_TOTP_SECRET`
- `KEYCLOAK_ADMIN_PASSWORD`
- `KEYCLOAK_B2B_CLIENT_SECRET`
- `OIDC_ISSUER_URL`
- `OIDC_AUDIENCE`
- `OIDC_CLIENT_ID`
- `OIDC_JWKS_URL`
- `OIDC_AUTHORIZATION_URL`

### Flags Esperadas de Ambiente

```bash
export APP_ENV=staging
export AUTH_MODE=oidc
export DEV_AUTH_ENABLED=false
export NEXT_PUBLIC_AUTH_MODE=oidc
export NEXT_PUBLIC_APP_ENV=staging
export NEXT_PUBLIC_DEV_AUTH_ENABLED=false
```

## Sequencia de Execucao Segura

### 1. Preflight de Ambiente Serio

Executar o preflight canonico de `OIDC`:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/preflight_oidc_serious_env.py
```

Esperado:

- `status=ok`
- `AUTH_MODE=oidc`
- `DEV_AUTH_ENABLED=false`
- endpoints OIDC reais, nunca `localhost`

### 2. Smoke Pos-Deploy

Executar a verificacao curta de runtime:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/smoke_auth_oidc_mode.py
```

Esperado:

- `ONTRACKCHAIN_EXPECTED_AUTH_MODE=oidc`
- `ONTRACKCHAIN_EXPECTED_EFFECTIVE_AUTH_MODE=oidc`
- `ONTRACKCHAIN_EXPECTED_APP_ENV=staging`
- nenhuma queda silenciosa para `dev auth`

### 3. E2E Critico

Executar o gate funcional do frontend:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain/apps/frontend
npm ci
npm run test:e2e:oidc-critical
```

Esperado:

- `/auth/config` coerente com ambiente serio
- fluxo federado critico verde

### 4. Bundle OIDC

Gerar o pacote operacional da trilha:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make run-oidc-readiness-bundle-local \
  WINDOW_ID=<window_id> \
  BASE_URL=http://localhost:8080
```

Esperado:

- `artifacts/staging/checks/<window_id>-oidc-readiness-bundle.json`
- `artifacts/staging/dossiers/<window_id>-oidc-readiness-bundle.md`
- o JSON do bundle deve explicitar `readiness.readiness_status` em `blocked`, `ready` ou `ready_for_validation`
- o markdown do bundle deve listar `Bloqueadores de Readiness` e `Proximo Passo` coerentes com a situacao da janela
- o `release dossier`, o draft de `sign-off` e a governanca semanal da janela devem refletir o mesmo `readiness_status`, para que `P0-01` possa ser promovido por evidencia e nao apenas por leitura manual dos steps tecnicos

### 5. Evidencia Externa Quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true`

Executar somente quando houver homologacao externa real:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/homologation_external_evidence.py --mode both --include-oidc-legal-report
```

Esperado:

- artefato de homologacao preservado
- prova auditada de fluxo sensivel com `MFA` externo

### 6. Reconciliar Governanca Semanal

Depois que os artefatos existirem, sincronizar a janela:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make refresh-staging-war-room-governance-local WINDOW_ID=<window_id>
```

Esperado:

- reducao objetiva de bloqueios no snapshot e delta
- artefatos da janela em `docs/governance-weekly/generated/windows/<window_id>/`
- consolidado pronto para gate, Slack e trilha executiva

## Artefatos Minimos Exigidos

- saida verde do `preflight_oidc_serious_env.py`
- saida verde do `smoke_auth_oidc_mode.py`
- `artifacts/staging/checks/<window_id>-oidc-readiness-bundle.json`
- `artifacts/staging/dossiers/<window_id>-oidc-readiness-bundle.md`
- relatorio do `test:e2e:oidc-critical`
- quando aplicavel, homologacao externa preservada para `MFA`
- snapshot/governanca atualizados apos `refresh-staging-war-room-governance-local`

## Criterio de Promocao de Status

Mover `P0-01` de `blocked` para `in_progress` somente quando:

- owner `Auth/OIDC` estiver confirmado
- secrets reais estiverem disponiveis
- a janela de homologacao estiver reservada

Mover `P0-01` para `ready_for_validation` somente quando:

- `preflight_oidc_serious_env.py` estiver verde
- `smoke_auth_oidc_mode.py` estiver verde
- o bundle OIDC tiver sido gerado
- o gate critico do frontend tiver sido executado
- a governanca semanal tiver sido reprocessada com os paths reais

Considerar `P0-01` fechado somente quando:

- os fluxos sensiveis exigirem auth serio sem fallback silencioso
- `MFA` estiver coerente com a politica homologada da janela
- os artefatos forem revisados por humano
- o accountable aceitar formalmente a janela

## Falhas Aceitaveis

- indisponibilidade controlada do IdP durante a janela
- ambiente serio configurado, mas `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=false`

Nesses casos:

- marcar a homologacao como nao concluida para o modo externo
- nao promover maturidade alem da evidencia realmente exercitada
- preservar artefatos para reexecucao

## Anti-Patterns

- nao aceitar fallback silencioso para `dev auth`
- nao promover `P0-01` apenas porque o scaffold OIDC local funciona
- nao registrar `done` sem bundle OIDC e smoke serio
- nao assumir homologacao externa de `MFA` sem prova revisavel

## Definicao de Pronto Operacional

`P0-01` esta pronto para aprovacao somente se houver:

- ambiente serio coerente
- preflight e smoke verdes
- bundle OIDC preservado
- gate critico do frontend executado
- governanca sincronizada
- aceite humano formal
