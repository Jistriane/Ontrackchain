# Pacote de Execução da Primeira Janela Séria

## Objetivo

Fornecer comandos copy/paste e uma lista de saídas esperadas para executar a primeira janela séria com evidências anexáveis, sem expor secrets.

Este pacote é orientado aos itens:

- `P0-01`
- `P0-05`
- `P0-06`
- `RUN-STG-01`

Referências canônicas:

- [Checklist de Evidência Mínima da Primeira Janela Séria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/first-serious-window-evidence-checklist.md)
- [Plano Operacional da Primeira Janela Séria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/first-serious-window-operational-plan.md)
- [Deploy e Staging](file:///home/jistriane/Ontracktchain/ontrackchain/docs/deploy-and-staging.md)
- [Ownership do `.env.staging`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/staging-env-ownership.md)

## Parâmetros

Defina o `window_id`:

- `stg-YYYYMMDD-a`

Exemplo:

- `stg-2026-06-29-a`

## Entradas Mínimas

Antes de rodar qualquer comando:

- `.env.staging.private` existe e não contém `__FILL_*__`
- `docs/staging-env-ownership.md` tem `Registro de Handoff` sem `pending`
- secrets e endpoints usados na janela foram confirmados pelos owners

## Execução (recomendado)

### 1. Criar o arquivo privado

```bash
cp .env.staging.example .env.staging.private
```

Preencha manualmente os placeholders em canal seguro.

### 2. Atualizar handoff

Edite `docs/staging-env-ownership.md` em `## Registro de Handoff` e substitua `pending` por valores coerentes.

### 3. Rodar a janela completa

```bash
python scripts/run_staging_window.py \
  --window-id stg-YYYYMMDD-a \
  --private-env-file .env.staging.private
```

## Saídas Esperadas (arquivos)

### Checks locais

Devem existir:

- `artifacts/staging/checks/ownership-coverage-<window_id>.json`
- `artifacts/staging/checks/placeholders-<window_id>.json`
- `artifacts/staging/checks/handoff-<window_id>.json`
- `artifacts/staging/checks/oidc-preflight-<window_id>.json`
- `artifacts/staging/checks/external-preflight-<window_id>.json`
- `artifacts/staging/checks/homologation-<window_id>.json`

### Packet da janela (redigido)

Deve existir:

- `artifacts/staging/window-packet-<window_id>.md`

### Homologação externa (anexável)

Deve existir:

- `artifacts/homologation/external_homologation_<mode>_<stamp>.json`
- `artifacts/homologation/external_homologation_<mode>_<stamp>.json.manifest.json`

### Dossier final (anexável)

Deve existir:

- `artifacts/staging/dossiers/staging_release_dossier_<window_id>_<stamp>.json`
- `artifacts/staging/dossiers/staging_release_dossier_<window_id>_<stamp>.json.manifest.json`

## Go/No-Go

Considerar a janela como executada apenas quando:

- o JSON final do runner tiver `status="ok"`
- o `release_dossier.status` estiver `ok`
- os manifests existirem e estiverem referenciados no dossier

Se qualquer etapa falhar:

- manter a janela como `ready` ou `in_progress`
- nunca como `done`
- registrar bloqueio com dependência externa quando aplicável

## Encerramento (governança)

1. Atualizar o registro semanal em:
   - [Registros Semanais de Governança](file:///home/jistriane/Ontracktchain/ontrackchain/docs/governance-weekly/README.md)
2. Atualizar a matriz operacional:
   - [Matriz Operacional de Execução para 95%](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-operational-execution-board.md)
3. Anexar no sign-off:
   - dossier final + manifesto
   - window packet
   - homologação + manifesto

## Suposições

- este pacote não substitui o checklist canônico
- a primeira janela séria deve privilegiar evidência e rastreabilidade, não velocidade
