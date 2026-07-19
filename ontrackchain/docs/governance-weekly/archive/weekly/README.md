# Historico Semanal

## Objetivo

Agrupar registros semanais fechados, atualizacoes de KPI e checks de readiness de semanas anteriores.

## Papel Nesta Taxonomia

Esta pasta guarda snapshots semanais ja encerrados e arquivados. Ela nao substitui:

- `../../README.md` como trilha datada viva de governanca
- `../../cycles/` como navegacao operacional ainda relevante por data
- `../../../README.md` como indice canonico da documentacao viva

Quando houver conflito, use esta precedencia:

1. `../../../README.md` e documentos canonicamente indexados
2. `../../cycles/` para ciclos ainda navegaveis ou ativos
3. `../weekly/` apenas como historico semanal arquivado

## Politica de Retencao

- manter apenas os ultimos `90 dias` de snapshots nesta pasta
- remover snapshots mais antigos quando ultrapassarem a janela de retencao
- tratar a trilha viva como: `docs/` + `governance-weekly/cycles/`

## Execucao

Rodar a limpeza sob demanda pela raiz tecnica do workspace:

```bash
cd /home/jistriane/Ontrackchain/github_main/ontrackchain
make prune-governance-weekly-archive GOVERNANCE_WEEKLY_ARCHIVE_RETENTION_DAYS=90
```

## Documentos Disponiveis

- [Governança Semanal — 2026-06-29](./2026-06-29-weekly-governance.md)
- [Governança Semanal — 2026-06-30](./2026-06-30-weekly-governance.md)
- [Atualização de KPI — 2026-07-01](./2026-07-01-kpi-scorecard-update.md)
- [Readiness Check da Janela Seria — 2026-07-01](./2026-07-01-staging-serious-window-readiness-check.md)
- [Governança Semanal — 2026-07-01](./2026-07-01-weekly-governance.md)
- [Governança Semanal — 2026-07-02](./2026-07-02-weekly-governance.md)
- [Governança Semanal — 2026-07-03](./2026-07-03-weekly-governance.md)

## Regra de Leitura

- trate todos os arquivos desta pasta como snapshots historicos arquivados
- use `cycles/` para navegacao operacional por data e `docs/` para a fonte canônica viva
- quando um arquivo arquivado divergir do estado atual, prevalecem os scorecards, boards e runbooks mais recentes
- se um snapshot antigo ainda for citado por valor de auditoria, referencie-o explicitamente como corte historico e nao como baseline viva
