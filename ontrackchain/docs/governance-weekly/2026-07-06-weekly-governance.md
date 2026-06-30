# Governança Semanal — 2026-07-06

## Leitura do Ciclo

- Baseline técnica: `89%`
- Readiness regulatório: `76%`
- Foco da semana: executar a primeira janela séria com evidências anexáveis e dossier final

## Contexto da Janela Séria

- `window_id`: `stg-2026-07-06-a`
- `mode`: `baseline`
- `environment_name`: `staging-serious`
- run do GitHub Actions: `pending`
- status esperado: `RUN-STG-01` de `ready -> in_progress` ou `ready -> done` (apenas se dossier final estiver `ok`)
- checklist canônico:
  - [Checklist de Evidência Mínima da Primeira Janela Séria](../first-serious-window-evidence-checklist.md)
- runbook do primeiro disparo:
  - [Runbook do Primeiro Disparo Real](../first-serious-window-first-dispatch-runbook.md)
- template de sign-off:
  - [Template de Sign-Off da Janela Seria](../staging-serious-window-signoff-template.md)
- sign-off desta janela:
  - [Sign-Off da Janela `stg-2026-07-06-a`](2026-07-06-staging-serious-window-signoff.md)

## Evidências Revisadas

- artifact `serious-staging-window-stg-2026-07-06-a`: `pending`
- overall status: `pending`
- validation status: `pending`
- preflight status: `pending`
- run status: `pending`
- window packet: `pending`
- dossier: `pending`
- homologation: `pending`

## Itens Atualizados

- ID: `P0-01`
  - status anterior:
  - status atual:
  - owner nominal:
  - artefato revisado:
  - próxima evidência esperada:

- ID: `P0-05`
  - status anterior:
  - status atual:
  - owner nominal:
  - artefato revisado:
  - próxima evidência esperada:

- ID: `P0-06`
  - status anterior:
  - status atual:
  - owner nominal:
  - artefato revisado:
  - próxima evidência esperada:

- ID: `RUN-STG-01`
  - status anterior: `ready`
  - status atual: `pending_execucao`
  - owner nominal: `Release Manager Tecnico`
  - artefato revisado: workflow `Staging Serious Window` + artifact `serious-staging-window-stg-2026-07-06-a`
  - próxima evidência esperada: sign-off preenchido com `overall status=ok`, `validation=ok`, `preflight=ok` e `run=ok`

## Itens Blocked

- ID:
  - motivo:
  - dependência externa:
  - owner da escalação:

## Decisões

- a semana fica orientada a executar a primeira janela séria via GitHub Actions, usando `mode=baseline` salvo bloqueio regulatório específico
- o artifact do workflow será tratado como evidência oficial de `RUN-STG-01`

## Ações da Próxima Semana

- executar o workflow `Staging Serious Window` para `stg-2026-07-06-a`
- preencher o sign-off em [Sign-Off da Janela `stg-2026-07-06-a`](2026-07-06-staging-serious-window-signoff.md)
- atualizar este registro com links reais de artifact, dossier e homologation

## Observações

- este registro deve capturar paths dos artefatos gerados na execução da janela, incluindo homologação e dossier
- se o run falhar, registrar explicitamente o ponto de falha (`validation`, `preflight` ou `run`) e o owner da escalacao
