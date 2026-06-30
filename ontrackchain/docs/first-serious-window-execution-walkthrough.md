# Passo a Passo Executável da Primeira Janela Séria

## Objetivo

Executar a primeira janela séria com evidências anexáveis e registrar, sem fricção, os paths produzidos pelo runner no registro semanal.

Este passo a passo é um complemento operacional do pacote e do checklist:

- [Checklist de Evidência Mínima da Primeira Janela Séria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/first-serious-window-evidence-checklist.md)
- [Pacote de Execução da Primeira Janela Séria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/first-serious-window-command-pack.md)
- [Plano Operacional da Primeira Janela Séria](file:///home/jistriane/Ontracktchain/ontrackchain/docs/first-serious-window-operational-plan.md)

## Regra de Segurança

- nunca registrar secrets em markdown
- não commitar `.env.staging.private`
- o registro semanal deve conter apenas paths e hashes/manifests gerados

## Parâmetros

Defina o `window_id` do dia:

- `stg-2026-06-30-a`

Arquivo privado:

- `.env.staging.private`

## Preparação (antes de rodar)

### 1. Criar o arquivo privado

```bash
cp .env.staging.example .env.staging.private
```

### 2. Preencher placeholders por owner

Distribuir e preencher conforme:

- [Ownership do `.env.staging`](file:///home/jistriane/Ontracktchain/ontrackchain/docs/staging-env-ownership.md)

Regra:

- nenhum `__FILL_*__` pode permanecer

### 3. Atualizar handoff

No arquivo:

- `docs/staging-env-ownership.md`

Em:

- `## Registro de Handoff`

Trocar `pending` por valores coerentes e status permitido.

## Execução (fluxo único)

### 4. Rodar a janela completa

```bash
python scripts/run_staging_window.py \
  --window-id stg-2026-06-30-a \
  --private-env-file .env.staging.private
```

Regra:

- se o runner retornar `status=failed`, não repetir em loop
- manter os artefatos gerados e registrar o motivo

## Colagem no Registro Semanal

Abrir o registro semanal do ciclo da janela e preencher os campos:

- `Evidências Revisadas`
- `Itens Atualizados`
- `Itens Blocked`

### 5. Capturar paths produzidos pelo runner

No JSON final impresso pelo runner, coletar:

- `steps.ownership_coverage.output_file`
- `steps.window_packet.output_file`
- `steps.placeholder_check.output_file`
- `steps.handoff_check.output_file`
- `steps.oidc_preflight.output_file`
- `steps.external_preflight.output_file`
- `steps.homologation.output_file`
- `steps.homologation.artifact_file`
- `steps.homologation.manifest_file`
- `steps.release_dossier.artifact_file`
- `steps.release_dossier.manifest_file`

### 6. Preencher as evidências no registro semanal

Em `## Evidências Revisadas`, colar:

- paths dos checks em `artifacts/staging/checks/`
- `window packet` em `artifacts/staging/`
- homologação e manifest em `artifacts/homologation/`
- dossier e manifest em `artifacts/staging/dossiers/`

Em `## Itens Atualizados`, para cada item, colar:

- `P0-01`: referenciar `oidc-preflight` e smoke/e2e quando aplicável
- `P0-05`: referenciar `homologation` com parte compliance e manifest
- `P0-06`: referenciar `homologation` com parte rpc e manifest
- `RUN-STG-01`: referenciar o dossier final e seu manifest

## Go/No-Go (fechamento)

Declarar a janela como executada apenas se:

- o JSON final tiver `status="ok"`
- `steps.release_dossier.status="ok"`
- existem os manifests de homologação e de dossier

Se `não`:

- manter `RUN-STG-01` como `ready` ou `in_progress`
- marcar bloqueio externo quando aplicavel

## Atualizações Pós-Janela

1. atualizar a matriz operacional:
   - [Matriz Operacional de Execução para 95%](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-operational-execution-board.md)
2. atualizar o board estratégico apenas se a leitura macro mudou:
   - [Board de Prioridades do Projeto](file:///home/jistriane/Ontracktchain/ontrackchain/docs/project-priority-board.md)

## Suposições

- a janela do dia usa `stg-2026-06-30-a` como `window_id`
- os owners já possuem canal seguro de troca de secrets
- o objetivo é produzir evidências anexáveis, não aprovar por atalho
