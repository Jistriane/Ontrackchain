# Guia de Execucao Assistida - `P0-03` Feed UE real

## Objetivo

Concentrar em um unico artefato o rito minimo para mover `P0-03` de `ready` para `in_progress`, executar a homologacao do feed UE tokenizado com evidencia preservada e devolver a trilha para a governanca semanal sem drift.

## Quando Usar

- quando a URL XML tokenizada oficial do feed da UE ja estiver disponivel fora do repositorio
- quando a janela seria incluir `P0-03` isolado ou combinado com `P0-02`
- quando o owner `Compliance/Backend` estiver nominalmente confirmado em `docs/staging-env-ownership.md`

## Fontes Canonicas

- [Runbook 16C](../../runbooks.md)
- [Project Release Gates](../../project-release-gates.md)
- [Project Operational Execution Board](../../project-operational-execution-board.md)
- [Staging Env Ownership](../../staging-env-ownership.md)
- [Plano Consolidado ate 95%](../../project-construction-plan-to-95-percent.md)

## Artefato Complementar

- [Run Sheet Operacional de `P0-03` Feed UE real](./P0-03_EU_FEED_RUN_SHEET.md)

## Estado Inicial Esperado

- `P0-03` ainda esta em `ready`
- a URL `COMPLIANCE_EU_SANCTIONS_SOURCE_URL` nao aparece em arquivo versionado
- o baseline local nao prova feed UE real sem override serio de ambiente
- a janela nao pode promover maturidade sem JSONs persistidos e checker pos-sync verde

## Requisitos Minimos

### Owner e Handoff

- grupo: `Compliance/AML`
- owner esperado: `Compliance/Backend`
- apoio: `Security`
- atualizar somente `date` e `status` em `docs/staging-env-ownership.md`

### Segredos Obrigatorios

Preencher apenas em `.env.staging.private` local ou no ambiente serio equivalente:

- `COMPLIANCE_EU_SANCTIONS_SOURCE_URL`
- `DATABASE_URL`

### Validacoes Obrigatorias do Override

- a URL deve usar `https`
- a URL deve conter `token=`
- o `DATABASE_URL` deve apontar para o banco do ambiente-alvo

## Sequencia de Execucao Segura

### 1. Preflight Externo

Executar antes do sync:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python3 scripts/preflight_external_integrations.py
```

Esperado:

- `status=ok`
- URL UE reconhecida como presente e tokenizada
- nenhum uso de URL local para ambiente serio

### 2. Reexecutar o Worker de Compliance

Executar com a env privada atualizada:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make rerun-compliance-worker
```

Esperado:

- worker reprocessado com a URL UE correta
- tentativa real de sync de `EU_CONSOLIDATED`

### 3. Executar a Janela UE

Preferir o runner completo:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make run-eu-sanctions-window-local WINDOW_ID=<window_id>
```

Alternativamente, se precisar isolar:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make run-eu-sanctions-window \
  WINDOW_ID=<window_id> \
  PRIVATE_ENV_FILE=.env.staging.private \
  CHECKS_DIR=artifacts/staging/checks
```

Esperado:

- `artifacts/staging/checks/<window_id>-eu-sanctions-preflight.json`
- `artifacts/staging/checks/<window_id>-eu-sanctions-sync.json`
- preservar o `request_id` da janela UE para correlacao entre runner, bundle regulatorio, janela seria e dossier

### 4. Checker Pos-Sync

Confirmar a convergencia final:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make check-eu-sanctions-window
```

Esperado:

- `EU_CONSOLIDATED.status=ACTIVE`
- `EU_CONSOLIDATED.last_sync_status=SUCCESS`
- `sanctions_lists_meta.source_url` igual ao override configurado
- o checker deve preservar `request_id` e `source_url` observada de `EU_CONSOLIDATED` para reconciliacao executiva
- o checker deve expor correlacao estruturada com `override_tokenized=true`
- o checker deve expor correlacao estruturada com `persisted_status_active=true`
- o checker deve expor correlacao estruturada com `last_sync_status_success=true`
- o checker deve expor correlacao estruturada com `eu_window_converges_ready=true`

### 5. Bundle Regulatorio Quando `P0-02` Tambem Estiver no Escopo

Se a mesma janela incluir `AML/KYT live`, preferir consolidar:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make run-regulatory-readiness-bundle-local WINDOW_ID=<window_id>
```

Esperado:

- `artifacts/staging/checks/<window_id>-regulatory-readiness-bundle.json`
- `artifacts/staging/dossiers/<window_id>-regulatory-readiness-bundle.md`
- o bundle deve preservar `steps.eu_sanctions_window.request_id`
- o bundle deve refletir `expected_source_url`, `observed_source_url`, `source_url_matches_expected`, `override_tokenized`, `persisted_status_active`, `last_sync_status_success` e `eu_window_converges_ready`

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

- saida verde do `preflight_external_integrations.py`
- `artifacts/staging/checks/<window_id>-eu-sanctions-preflight.json`
- `artifacts/staging/checks/<window_id>-eu-sanctions-sync.json`
- `make check-eu-sanctions-window` verde
- `EU_CONSOLIDATED` em `ACTIVE/SUCCESS`
- `source_url` persistido igual ao override configurado
- `request_id` da janela UE preservado nos artefatos executivos
- correlacao estruturada com `eu_window_converges_ready=true`
- quando aplicavel, `regulatory-readiness-bundle.json` e resumo `.md`
- snapshot/governanca atualizados apos `refresh-staging-war-room-governance-local`

## Criterio de Promocao de Status

Mover `P0-03` de `ready` para `in_progress` somente quando:

- a URL UE tokenizada real estiver disponivel
- o owner `Compliance/AML` estiver confirmado
- a janela de homologacao estiver reservada

Mover `P0-03` para `ready_for_validation` somente quando:

- os dois JSONs da janela UE tiverem sido gerados
- o checker `check-eu-sanctions-window` estiver verde
- `EU_CONSOLIDATED` estiver convergente no banco
- a governanca semanal tiver sido reprocessada com os paths reais

Considerar `P0-03` fechado somente quando:

- a URL tokenizada tiver sido exercitada com sucesso
- os artefatos forem revisados por humano
- o accountable aceitar formalmente a janela

## Falhas Aceitaveis

- `403` da UE antes do provisionamento correto da URL tokenizada
- indisponibilidade temporaria do feed durante a janela

Nesses casos:

- marcar a homologacao como nao concluida
- registrar o erro explicitamente no checker, no `status_reason` ou na trilha da janela
- nao promover maturidade

## Anti-Patterns

- nao preencher a URL tokenizada em documentos versionados
- nao tratar override divergente como sucesso parcial
- nao promover `P0-03` apenas porque o runner existe
- nao registrar `done` sem os dois JSONs da janela e checker verde

## Definicao de Pronto Operacional

`P0-03` esta pronto para aprovacao somente se houver:

- URL tokenizada real validada no ambiente correto
- worker reexecutado com a env atualizada
- JSONs da janela UE preservados
- checker pos-sync verde
- governanca sincronizada
- aceite humano formal
