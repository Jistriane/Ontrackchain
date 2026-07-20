# Resumo de Comunicacao - stg-2026-07-20-a

## Bloco Curto (Slack/Teams)

Janela stg-2026-07-20-a: status `failed` | semaforo `unknown`.
Escopo regulatorio: `none` | `P0-04` readiness: `unknown`.
Classificacao dominante: `technical_gate_blocked` | resumo: falha tecnica registrada em prepare, run, artifact_validation
RCA cross-domain: `0` RCA(s) em `0` work-item(s) rastreado(s) | pendente `0` | criticos `0`.
Bloqueios: `0` placeholders e `0` handoff.
Steps: prepare `failed`, run `failed`, artifact `failed`.
Leitura: delta indisponivel
Leitura regulatoria: sem escopo regulatorio material nesta tentativa
Acao: owners por trilha devem executar o checklist de desbloqueio e rerodar o comando unico.

## Mensagem Expandida

- janela: `stg-2026-07-20-a`
- snapshot: `artifacts/staging/checks/stg-2026-07-20-a-status-snapshot.json`
- status geral: `failed`
- semaforo executivo: `unknown`
- leitura do delta: delta indisponivel
- escopo regulatorio da tentativa: `none`
- scope validado no gate final: `P0-01,P0-02,P0-03`
- `P0-04` readiness: `unknown`
- leitura regulatoria: sem escopo regulatorio material nesta tentativa
- classificacao dominante: `technical_gate_blocked`
- resumo do bloqueio dominante: falha tecnica registrada em prepare, run, artifact_validation
- resumo RCA disponivel: `not_available`
- incidentes exportados no resumo: `0`
- work-items rastreados: `0`
- RCAs anexadas: `0`
- causas confirmadas: `0`
- incidentes criticos abertos: `0`
- triagem pendente: `0`
- dominios RCA em destaque: `none`
- placeholders pendentes: `0`
- handoff pendente: `0`

Referencias para o war room:
- dashboard executivo: `docs/governance-weekly/generated/windows/stg-2026-07-20-a/stg-2026-07-20-a-governance-dashboard.md`
- checklist de desbloqueio: `docs/governance-weekly/generated/windows/stg-2026-07-20-a/stg-2026-07-20-a-unblock-checklist.md`
- checklist regulatorio consolidado: `artifacts/staging/dossiers/stg-2026-07-20-a-regulatory-unblock-checklist.md`
- delta de status: `docs/governance-weekly/generated/windows/stg-2026-07-20-a/stg-2026-07-20-a-status-snapshot-delta.md`

Comando unico:
- `make refresh-staging-war-room-governance-local WINDOW_ID=stg-2026-07-20-a`
