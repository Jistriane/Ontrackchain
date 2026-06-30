# Checklist de Evidência Mínima da Primeira Janela Séria

## Objetivo

Definir a evidência mínima necessária para considerar a primeira janela séria de `staging` como executada com honestidade operacional.

Este documento cobre especificamente:

- `P0-01`
- `P0-05`
- `P0-06`
- `RUN-STG-01`

Este checklist complementa:

- [Deploy e Staging](deploy-and-staging.md)
- [Gates de Release para Staging Sério](project-release-gates.md)
- [Matriz Operacional de Execução para 95%](project-operational-execution-board.md)
- [Runbook de Governança Semanal](project-weekly-governance-runbook.md)
- [Runbook do Primeiro Disparo Real](first-serious-window-first-dispatch-runbook.md)
- [Template de Sign-Off da Janela Seria](staging-serious-window-signoff-template.md)

## Regra Mestra

A primeira janela séria só pode ser tratada como executada quando houver:

1. critério de entrada atendido
2. execução real em ambiente sério
3. artefatos persistidos
4. critério de saída atendido

Não contam como execução séria:

- validação apenas local
- simulação manual sem artefato
- print solto sem correlação
- sucesso parcial sem dossier final
- provider configurado, mas não homologado
- disparo fora do workflow oficial sem pacote de artefatos equivalente

## Janela Alvo

Janela alvo recomendada:

- `stg-YYYY-MM-DD-a`

Artefatos obrigatórios esperados ao final:

- `artifacts/staging/checks/ownership-coverage-<janela>.json`
- `artifacts/staging/checks/placeholders-<janela>.json`
- `artifacts/staging/checks/handoff-<janela>.json`
- `artifacts/staging/window-packet-<janela>.md`
- `artifacts/homologation/<artefato>.json`
- `artifacts/homologation/<artefato>.json.manifest.json`
- `artifacts/staging/dossiers/<dossier>.json`
- `artifacts/staging/dossiers/<dossier>.manifest.json`
- artifact `serious-staging-window-<janela>` do workflow manual ou pacote equivalente anexado ao sign-off

## Fluxo Operacional Canônico

Para a primeira janela via GitHub Actions, usar:

```bash
make prepare-serious-window-dispatch \
  WINDOW_ID="stg-2026-07-06-a"
```

Depois do run oficial e do download do artifact, fechar com:

```bash
make postprocess-serious-window \
  RUN_URL="https://github.com/<org>/<repo>/actions/runs/<run_id>"
```

O pacote gerado em `ci-artifacts/` e a copia versionada em `docs/governance-weekly/` passam a ser a base oficial do sign-off humano.

## Checklist por Item

### 1. `P0-01` — OIDC serio fora do local

#### Criterio de Entrada — `P0-01`

- `.env.staging.private` preenchido sem placeholders
- `AUTH_MODE=oidc`
- `DEV_AUTH_ENABLED=false`
- URLs publicas de `OIDC` fora de `localhost`
- claims organizacionais e de papel definidos
- quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true`, `ONTRACKCHAIN_HOMOLOGATION_OIDC_TOKEN` disponivel para evidência funcional do `legal_report`

#### Evidencia Minima de Execucao — `P0-01`

- `python scripts/preflight_oidc_serious_env.py` com `status=ok`
- `python scripts/smoke_auth_oidc_mode.py` com `effective_auth_mode=oidc`
- login real funcional em ambiente serio
- protecao de rota administrativa exercitada sem fallback para `dev auth`
- artefato de `playwright` critico verde no trilho `OIDC`
- quando `MFA_EXTERNAL_PROVIDER_HOMOLOGATED=true`, `python scripts/homologation_external_evidence.py --mode both --include-oidc-legal-report` com download `200` e `report_downloaded` auditado

#### Criterio de Saida — `P0-01`

- existe prova de autenticacao federada real
- existe prova de enforcement administrativo no ambiente serio
- nao existe dependencia operacional de `AUTH_MODE=dev`
- quando houver homologacao de MFA federado, existe prova anexavel de `legal_report` auditado ponta a ponta

#### Bloqueadores Classicos — `P0-01`

- segredo nao-dev ausente
- issuer ou authorization URL ainda local
- login funcionando apenas no ambiente local
- autenticação visualmente valida, mas sem prova de backend em modo `oidc`

### 2. `P0-05` — AML/KYT real em modo `live`

#### Criterio de Entrada — `P0-05`

- contrato ou acesso operacional ao provider disponivel
- credenciais validas no `.env.staging.private`
- `COMPLIANCE_TRM_ENABLED=true`
- expectativa de modo definida como `live`

#### Evidencia Minima de Execucao — `P0-05`

- `python scripts/preflight_external_integrations.py` com expectativa `compliance=live`
- `provider-readiness` em modo `live`
- `python scripts/homologation_external_evidence.py --mode compliance` ou `--mode both`
- artefato de homologacao com `request_id` correlacionado
- evidência de `/audit` anexada ao bundle
- resposta controlada de degradacao, erro ou timeout documentada quando ocorrer

#### Criterio de Saida — `P0-05`

- provider AML/KYT operando com chamada real ou homologacao externa controlada
- trilha auditavel por `request_id`
- evidencias persistidas em artefato e manifesto

#### Bloqueadores Classicos — `P0-05`

- retorno stub disfarcado de sucesso real
- readiness verde sem chamada homologada
- provider configurado, mas sem bundle anexavel
- degradacao silenciosa sem telemetria clara

### 3. `P0-06` — RPC primario com fallback homologado

#### Criterio de Entrada — `P0-06`

- `INVESTIGATION_RPC_ENABLED=true`
- `INVESTIGATION_RPC_PRIMARY_URL` e `INVESTIGATION_RPC_FALLBACK_URL` definidos
- expectativa de modo definida como `live` ou `fallback_only`
- timeout e retry coerentes com a janela

#### Evidencia Minima de Execucao — `P0-06`

- `python scripts/preflight_external_integrations.py` validando `rpc=live|fallback_only`
- `rpc-readiness` com `ready=true`
- `details.operating_mode=live|fallback_only`
- `python scripts/homologation_external_evidence.py --mode rpc` ou `--mode both`
- artefato com correlação de `request_id`
- evidência de resultado final preservando metadados de provider no fluxo de investigation

#### Criterio de Saida — `P0-06`

- investigation usa RPC real com fallback previsivel
- existe evidência de readiness e homologacao anexavel
- modo operacional real do provider ficou preservado no resultado da cadeia

#### Bloqueadores Classicos — `P0-06`

- fallback configurado apenas no papel
- readiness verde sem bundle real de homologacao
- investigacao sem metadados do provider no resultado final
- endpoint aceito apenas em ambiente local

### 4. `RUN-STG-01` — Primeira janela seria completa

#### Criterio de Entrada — `RUN-STG-01`

- `P0-01`, `P0-05` e `P0-06` com ambiente minimo pronto para execucao
- matriz de ownership e handoff atualizada
- arquivo privado sem placeholders
- janela identificada por `window_id`

#### Evidencia Minima de Execucao — `RUN-STG-01`

- `python scripts/prepare_staging_window.py --window-id <janela> --mode baseline|homologated --run` ou workflow manual `Staging Serious Window`
- JSONs dos checks persistidos
- `window packet` gerado
- homologacao externa gerada
- dossier final gerado com manifesto
- `status=ok` no dossier final apenas se todos os componentes verdes

#### Criterio de Saida — `RUN-STG-01`

- existe cadeia completa de evidencias da janela
- existe dossier anexavel para sign-off
- a janela pode ser revisada sem depender de relato verbal

#### Bloqueadores Classicos — `RUN-STG-01`

- execução parcial fora do runner oficial
- checks rodados sem persistência dos JSONs
- homologacao sem dossier final
- dossier gerado com `failed` ou artefatos ausentes

## Sequencia Recomendada

1. preencher `.env.staging.private`
2. validar ownership, placeholders e handoff
3. validar `OIDC` serio
4. validar integrações externas
5. executar homologacao externa
6. consolidar dossier
7. registrar a semana no runbook de governanca

## Evidencia Minima por Fase

| Fase | Evidencia Minima |
| --- | --- |
| Entrada | `.env.staging.private`, ownership, handoff e placeholders verdes |
| Execucao | preflights `OIDC` e integrações externas verdes |
| Homologacao | artefato `.json` + `.manifest.json` em `artifacts/homologation/` |
| Consolidacao | dossier final `.json` + `.manifest.json` em `artifacts/staging/dossiers/` |
| Governanca | registro semanal atualizado com bloqueios, decisões e próximos passos |

## Perguntas de Go/No-Go

Antes de declarar a primeira janela seria como executada, responder:

1. houve autenticação federada real em ambiente serio?
2. houve homologacao AML/KYT real ou controlada com bundle anexavel?
3. houve homologacao RPC real ou controlada com bundle anexavel?
4. o runner `run_staging_window.py` produziu dossier final utilizavel?
5. existe alguma dependencia critica ainda escondida fora dos artefatos?
6. o artifact `serious-staging-window-<janela>` foi preservado ou referenciado no sign-off?

Se qualquer resposta for `nao`, a janela deve continuar como:

- `ready`
- ou `in_progress`

Nunca como `done`.

## Decisao Recomendada

- usar este checklist como o filtro minimo antes de promover `RUN-STG-01`
- nao contabilizar ganho adicional de maturidade apenas por readiness documental
- considerar a primeira janela seria encerrada apenas quando os quatro blocos acima tiverem evidência anexavel

## Suposicoes

- a primeira janela seria ainda nao ocorreu de forma completa
- o objetivo atual e provar execucao honesta, nao maximizar taxa de aprovacao
- os artefatos persistidos em `artifacts/` serao preservados ou anexados ao fluxo de sign-off
