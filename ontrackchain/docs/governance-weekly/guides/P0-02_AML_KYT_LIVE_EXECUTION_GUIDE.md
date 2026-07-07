# Guia de Execucao Assistida - `P0-02` AML/KYT live

## Objetivo

Concentrar em um unico artefato o rito minimo para mover `P0-02` de `ready` para `in_progress`, executar a homologacao `AML/KYT live` com evidencia preservada e devolver a trilha para a governanca semanal sem drift.

## Quando Usar

- quando a credencial real do provider AML/KYT ja estiver disponivel fora do repositório
- quando a janela seria incluir `P0-02` isolado ou combinado com `P0-03`
- quando o owner `Compliance/Backend` estiver nominalmente confirmado em `docs/staging-env-ownership.md`

## Fontes Canonicas

- [Runbook 16A](../../runbooks.md)
- [Project Release Gates](../../project-release-gates.md)
- [Project Operational Execution Board](../../project-operational-execution-board.md)
- [Staging Env Ownership](../../staging-env-ownership.md)
- [Execution Checklist to 95 Percent](../../EXECUTION_CHECKLIST_TO_95_PERCENT.md)

## Artefato Complementar

- [Run Sheet Operacional de `P0-02` AML/KYT live](./P0-02_AML_KYT_LIVE_RUN_SHEET.md)

## Estado Inicial Esperado

- `P0-02` ainda esta em `ready`
- o baseline local continua com `COMPLIANCE_TRM_ENABLED=false`
- nenhuma credencial real aparece em arquivo versionado
- a janela nao pode promover maturidade sem checker verde e artefato anexavel

## Requisitos Minimos

### Owner e Handoff

- grupo: `Compliance/AML`
- owner esperado: `Compliance/Backend`
- apoio: `Security`
- atualizar somente `date` e `status` em `docs/staging-env-ownership.md`

### Segredos Obrigatorios

Preencher apenas em `.env.staging.private` local ou no ambiente serio equivalente:

- `COMPLIANCE_TRM_ENABLED=true`
- `COMPLIANCE_TRM_SCREENING_URL`
- `COMPLIANCE_TRM_API_KEY`
- `COMPLIANCE_TRM_API_KEY_HEADER`
- `COMPLIANCE_TRM_API_KEY_PREFIX`
- `COMPLIANCE_TRM_TIMEOUT_MS`
- `COMPLIANCE_TRM_MAX_RETRIES`

### Variaveis de Shell Recomendadas

```bash
export ONTRACKCHAIN_EXPECT_COMPLIANCE_MODE=live
export ONTRACKCHAIN_EXPECT_RPC_MODE=disabled
```

## Sequencia de Execucao Segura

### 1. Preflight Externo

Executar antes de qualquer chamada real de homologacao:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python scripts/preflight_external_integrations.py
```

Esperado:

- `status=ok`
- modo de compliance coerente com `live`
- URL e credencial reconhecidas como presentes no ambiente privado

### 2. Gate Leve do Provider

Executar o gate canonico de runtime:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make check-compliance-provider-runtime \
  INTERNAL_BASE_URL=http://compliance-api:8002 \
  PUBLIC_BASE_URL=http://localhost:8080
```

Esperado:

- readiness interna `ready=true`
- `details.operating_mode=live`
- catalogo publico coerente com `kyc_wallet.provider=trm_labs`
- evidencia JSON preservavel no terminal ou no arquivo de execucao da janela

### 3. Smoke Runtime

Executar uma verificacao funcional curta:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python scripts/smoke_runtime.py
```

Esperado:

- checks de compliance relevantes verdes
- nenhuma degradacao silenciosa nao documentada

### 4. Evidencia Externa de Homologacao

Executar a coleta formal da trilha de homologacao:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
python scripts/homologation_external_evidence.py --mode compliance
```

Esperado:

- JSON em `artifacts/homologation/`
- manifesto correspondente `.manifest.json`
- `request_id` correlacionavel entre readiness, catalogo, `risk-check` e bundle `/audit`

### 5. Bundle Regulatório Quando `P0-03` Tambem Estiver no Escopo

Se a mesma janela incluir feed UE real, preferir consolidar:

```bash
cd /home/jistriane/Ontrackchain/ontrackchain
make run-regulatory-readiness-bundle-local WINDOW_ID=<window_id>
```

Esperado:

- `artifacts/staging/checks/<window_id>-regulatory-readiness-bundle.json`
- `artifacts/staging/dossiers/<window_id>-regulatory-readiness-bundle.md`

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
- gate verde de `make check-compliance-provider-runtime`
- artefato JSON de homologacao em `artifacts/homologation/`
- bundle `/audit` correlacionado pelo mesmo `request_id`
- quando aplicavel, `regulatory-readiness-bundle.json` e resumo `.md`
- snapshot/governance atualizados apos `refresh-staging-war-room-governance-local`

## Criterio de Promocao de Status

Mover `P0-02` de `ready` para `in_progress` somente quando:

- a credencial real do provider estiver disponivel
- o owner `Compliance/AML` estiver confirmado
- a janela de homologacao estiver reservada

Mover `P0-02` para `ready_for_validation` somente quando:

- o gate `check-compliance-provider-runtime` estiver verde
- a homologacao externa tiver gerado artefato anexavel
- os artefatos estiverem preservados em `artifacts/`
- a governanca semanal tiver sido reprocessada com os paths reais

Considerar `P0-02` fechado somente quando:

- readiness interna e catalogo publico convergirem em `live`
- a evidencia for revisada por humano
- o accountable aceitar formalmente a janela

## Falhas Aceitaveis

- indisponibilidade controlada do provider durante a janela
- `provider_status=degraded` com motivo explicito
- falha auditada com `request_id`

Nesses casos:

- marcar a homologacao como nao concluida
- nao promover maturidade
- preservar artefatos para reexecucao

## Anti-Patterns

- nao preencher segredos em documentos versionados
- nao promover `P0-02` apenas porque o codigo e o checker existem
- nao registrar `done` sem artefato anexavel
- nao atualizar scorecard antes de revisao humana e aceite formal

## Definicao de Pronto Operacional

`P0-02` esta pronto para aprovacao somente se houver:

- credencial real validada no ambiente correto
- checker verde
- homologacao externa preservada
- governanca sincronizada
- aceite humano formal
