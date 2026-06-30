# Plano Operacional da Primeira Janela Séria

## Objetivo

Executar a primeira janela séria de `staging` com evidência anexável, sem sucesso fictício, cobrindo:

- `P0-01` (OIDC sério)
- `P0-05` (AML/KYT em `live`)
- `P0-06` (RPC com `primary + fallback`)
- `RUN-STG-01` (janela completa com dossier)

Este plano complementa:

- [Checklist de Evidência Mínima da Primeira Janela Séria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/first-serious-window-evidence-checklist.md)
- [Pacote de Execução da Primeira Janela Séria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/first-serious-window-command-pack.md)
- [Deploy e Staging](file:///home/jistriane/Ontracktchain/ontrackchain/docs/deploy-and-staging.md)
- [Ownership do `.env.staging`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/staging-env-ownership.md)
- [Gates de Release para Staging Sério](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-release-gates.md)

## Regra de Segurança

- este plano nunca inclui valores reais de secrets
- `.env.staging.private` deve ser tratado como arquivo sensível
- preenchimento de secrets deve ocorrer em canal seguro e com owners definidos

## Identificador da Janela

Escolher um `window_id` no formato:

- `stg-YYYYMMDD-a`

Exemplo:

- `stg-2026-06-29-a`

## Entradas (antes da janela)

### 1. Preencher `.env.staging.private`

```bash
cp .env.staging.example .env.staging.private
```

Distribuir placeholders por owner conforme:

- [Ownership do `.env.staging`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/staging-env-ownership.md)

### 2. Garantir handoff formal

- atualizar `docs/staging-env-ownership.md` em `## Registro de Handoff`
- evitar `pending` em qualquer linha

### 3. Preparar diretórios de artefatos

Recomendacao operacional:

- preservar o diretório `artifacts/` (nao limpar) durante a janela

## Execucao (preferencial)

### Fluxo Unico (recomendado)

Executar a janela completa pela orquestracao oficial:

```bash
python scripts/run_staging_window.py \
  --window-id stg-YYYYMMDD-a \
  --private-env-file .env.staging.private
```

Saidas esperadas (alto nivel):

- checks persistidos em `artifacts/staging/checks/`
- `window packet` em `artifacts/staging/`
- homologacao em `artifacts/homologation/`
- dossier final em `artifacts/staging/dossiers/`

## Evidencia Minima (por owner)

### Owner: Backend/Auth (P0-01 e P0-02)

Entregas minimas:

- `.env.staging.private` com:
  - `AUTH_MODE=oidc`
  - `DEV_AUTH_ENABLED=false`
  - URLs `OIDC_*` fora de `localhost`
- execucao valida do preflight OIDC (via runner)

Artefatos esperados:

- `artifacts/staging/checks/ownership-coverage-<janela>.json`
- `artifacts/staging/checks/placeholders-<janela>.json`
- `artifacts/staging/checks/handoff-<janela>.json`
- trecho do JSON consolidado da janela com `preflight_oidc_serious_env.status=ok` (quando aplicavel)

Critico:

- nao aceitar como evidencia apenas “login no browser”; deve existir prova de modo efetivo `oidc` (smoke) e preflight `ok`

### Owner: Compliance/Backend (P0-05)

Entregas minimas:

- provider configurado para `live` em `staging`
- preflight de integrações externas validado (via runner)
- homologacao externa executada para compliance

Artefatos esperados:

- `artifacts/homologation/external_homologation_both_*.json` (ou `compliance_*`)
- `artifacts/homologation/external_homologation_*.json.manifest.json`
- evidencias correlacionadas por `request_id`

Critico:

- `provider-readiness` em `live` deve ser acompanhado por evidência anexavel de homologacao, nao apenas por configuracao

### Owner: Backend Core (P0-06)

Entregas minimas:

- `INVESTIGATION_RPC_PRIMARY_URL` e `INVESTIGATION_RPC_FALLBACK_URL` validos
- modo esperado `live` ou `fallback_only` definido para a janela
- homologacao externa executada para RPC

Artefatos esperados:

- homologacao externa com parte `rpc`
- evidencias correlacionadas por `request_id`
- preservacao de metadados do provider no resultado final do fluxo de investigation (quando aplicavel)

Critico:

- fallback deve ser comprovado como comportamento previsivel, nao apenas como URL preenchida

### Owner: Platform/SRE e Platform/DBA (RUN-STG-01)

Entregas minimas:

- garantir que os checkers e o runner possam escrever em `artifacts/`
- garantir que o ambiente nao reutiliza defaults inseguros
- garantir que os artefatos finais existam e sejam anexaveis ao sign-off

Artefatos esperados:

- `artifacts/staging/window-packet-<janela>.md`
- `artifacts/staging/dossiers/staging_release_dossier_<janela>_*.json`
- `artifacts/staging/dossiers/staging_release_dossier_<janela>_*.json.manifest.json`

Critico:

- `status=ok` no dossier final so e valido quando checks e homologacao estiverem `ok`

### Owner: Security/Compliance (sign-off)

Entregas minimas:

- revisar evidencias anexadas
- registrar excecoes apenas se forem aceitaveis temporariamente (ver gates)

Artefatos esperados:

- referencia ao dossier final e ao manifest de integridade

## Saida (encerramento da janela)

### 1. Validar o checklist

- aplicar o [Checklist de Evidencia Minima da Primeira Janela Seria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/first-serious-window-evidence-checklist.md)

### 2. Atualizar governanca semanal

- registrar no historico semanal em:
  - [Registros Semanais de Governanca](file:///home/jistriane/Ontracktchain/ontrackchain/docs/governance-weekly/README.md)

### 3. Atualizar a matriz operacional

- promover `RUN-STG-01` apenas quando o dossier final estiver anexavel e `ok`

## Falhas e Tratamento

Se a janela falhar:

- nao reexecutar em loop sem registrar o motivo
- manter os artefatos gerados e anexar ao diagnostico
- marcar o item como `blocked` quando a dependencia for externa (credencial, provider, aceite formal)

## Suposicoes

- a janela ainda nao foi executada de forma completa com providers reais
- existe canal seguro para troca de secrets entre owners
- o objetivo e maximizar evidência e rastreabilidade, nao “passar de qualquer jeito”
