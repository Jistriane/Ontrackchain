# Registros Semanais de Governança

## Objetivo

Centralizar os registros gerados a partir do [Runbook de Governança Semanal](../project-weekly-governance-runbook.md).

## Papel Nesta Taxonomia

Nesta arvore vivem os artefatos datados de execucao, divididos em:

- `cycles/`: ciclos humanos ainda navegaveis por data
- `generated/`: artefatos gerados automaticamente, especialmente por `window_id`
- `archive/`: historico frio consolidado

Esta pasta nao substitui a baseline viva de `docs/`. Quando houver conflito, a precedencia continua sendo:

1. `../README.md` e os documentos canonicamente indexados nele
2. `cycles/` para prova datada por semana ou janela
3. `archive/` apenas como historico preservado

## Escopo Canônico

Use esta pasta para:

- registrar snapshots semanais, war rooms, tracking ao vivo, sign-offs e evidencias fechadas por ciclo
- preservar historico operacional e executivo sem sobrescrever o estado de semanas anteriores
- anexar a trilha documental de uma janela seria especifica depois que ela existir de fato

Não use esta pasta como fonte primária para:

- descrever o fluxo técnico canônico de deploy: use [Deploy e Staging](../deploy-and-staging.md)
- definir gates formais ou criterio executivo de promocao: use [Gates de Release para Staging Serio](../project-release-gates.md)
- manter checklists operacionais genericos sem contexto de ciclo: use os documentos canônicos em `docs/`

Cada arquivo desta pasta deve representar um ciclo semanal fechado, contendo:

- leitura do ciclo
- contexto da janela seria, quando aplicavel
- evidências revisadas
- itens atualizados
- itens `blocked`
- decisões
- ações da próxima semana

## Regra de Leitura

- considere como `ativo` apenas o ciclo corrente ainda em preparação ou execução
- trate ciclos datados anteriores como registro operacional fechado, mesmo quando permaneçam em `cycles/` por valor de consulta
- use `archive/` para histórico frio consolidado e `cycles/` para histórico operacional navegável por data
- use `generated/windows/<window_id>/` para payloads, dashboards e artefatos derivados gerados automaticamente, nunca como substituto da narrativa humana do ciclo

## Convenção de Nome

Formato recomendado dentro de `cycles/<data>/`:

- `YYYY-MM-DD-weekly-governance.md`

Exemplo:

- `cycles/2026-07-06/2026-07-06-weekly-governance.md`

## Regras de Uso

1. criar um novo arquivo por semana
2. não sobrescrever o registro da semana anterior
3. registrar apenas evidências reais revisadas no ciclo
4. manter alinhamento entre este registro, a [Matriz Operacional de Execução para 95%](../project-operational-execution-board.md) e o [Board de Prioridades do Projeto](../project-priority-board.md)
5. quando houver janela séria via GitHub Actions, registrar `window_id`, `environment_name`, link do run e artifact `serious-staging-window-<janela>`
6. usar [Resumo Executivo de Readiness](../project-executive-readiness-brief.md), [Scorecard Oficial](../project-kpi-scorecard.md) e [Avaliacao de Maturidade](../project-maturity-assessment.md) como baseline viva para discussoes de maturidade, subida para `95%` ou decisao de `go/no-go`
7. para qualquer decisão de `go`, anexar resultado do `validate_serious_window_artifact.py` com `status=ok` e `invalid_artifacts=[]` no war room, sign-off e registro semanal

Se precisar citar um parecer historico congelado para comparacao de momento, use [Avaliacao Consolidada de Status do Projeto](../assessments/PROJECT_STATUS_ASSESSMENT_2026_07_03.md) explicitamente como corte datado, nunca como baseline corrente.

## Comando Unico (War Room Local)

Para atualizar o pacote operacional local da janela seria em uma linha, usar:

- `make refresh-staging-war-room-governance-local WINDOW_ID=stg-YYYY-MM-DD-a`

Esse comando atualiza:

- plano de acao do war room
- snapshot consolidado (JSON + Markdown)
- delta entre os dois snapshots mais recentes
- dashboard executivo
- checklist de desbloqueio
- resumo de comunicação (Slack/Teams)
- resumo executivo de uma linha
- **JSON consolidado machine-readable** com toda a governança (para CI/CD gates, bots, dashboards)

Observacao importante:

- este comando atualiza apenas o pacote gerado em `docs/governance-weekly/generated/windows/<window_id>/`
- ele nao gera sozinho o `sign-off` versionado do ciclo nem o `go/no-go decision packet`
- para artefatos executivos derivados do payload consolidado, use o pós-processamento da janela séria

## Pos-Processamento Executivo da Janela

Quando existir `ci-artifacts/prepare-staging-window-output.json`, o fluxo canonico para sincronizar os artefatos humanos do ciclo e a leitura executiva e:

- `make postprocess-serious-window RUN_URL=https://github.com/<org>/<repo>/actions/runs/<run_id>`

Esse comando:

- atualiza `ci-artifacts/staging-serious-window-signoff.md`
- gera o sign-off versionado em `docs/governance-weekly/cycles/<data>/`
- gera o `go/no-go decision packet` versionado em `docs/governance-weekly/cycles/<data>/`
- sincroniza o registro semanal correspondente
- sincroniza o board operacional global a partir do mesmo payload consolidado

Para execucao local ponta a ponta, o atalho:

- `make run-serious-window-local WINDOW_ID=stg-YYYY-MM-DD-a MODE=baseline`

ja executa o pós-processamento automaticamente ao final do runner da janela.

### Notificação Slack (Opcional)

Para enviar o resumo de governança para Slack webhook:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
make notify-slack-governance WINDOW_ID=stg-YYYY-MM-DD-a
```

Ou durante o refresh completo (automaticamente skipado se webhook não estiver configurado):

```bash
make refresh-staging-war-room-governance-local \
  WINDOW_ID=stg-YYYY-MM-DD-a \
  SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

Opções:

- `--mention-on-red`: adiciona @channel quando sinal é vermelho
- `--channel`: canal Slack (default: governance)
- `--dry-run`: simula sem enviar (debug)

### CI/CD Gate Evaluation (Para CI/CD Pipelines)

Para avaliar se a governança permite uma operação CI/CD:

```bash
# Apenas merge allowed em VERDE + GO (strict)
make evaluate-governance-gate \
  WINDOW_ID=stg-YYYY-MM-DD-a \
  GATE_POLICY=strict \
  GATE_OPERATION=merge
```

Políticas de gate:

- `strict`: apenas VERDE + GO permite operação
- `moderate`: AMARELO + GO permite, VERMELHO bloqueia
- `relaxed`: qualquer estado permite (logging only)

Operações:

- `merge`: merge de código para main
- `deploy`: deployment para staging/production
- `release`: tagged release

Formatos:

- `--format json`: JSON com detalhes (default)
- `--format github`: variáveis para GitHub Actions
- `--format gitlab`: variáveis para GitLab CI
- `--exit-code`: retorna exit 0=allowed, 1=blocked

Exemplo de uso em CI/CD:

```bash
# GitHub Actions
make evaluate-governance-gate \
  WINDOW_ID=stg-YYYY-MM-DD-a \
  GATE_POLICY=strict \
  GATE_OPERATION=deploy \
  --format github --exit-code
```

## Mapa da Pasta

- [Índice de Guias Permanentes](guides/README.md)
- [Índice de Templates](templates/README.md)
- [Índice de Ciclos](cycles/README.md)
- [Índice de Artefatos Gerados](generated/README.md)
- [Índice do Arquivo Histórico](archive/README.md)

## Registros Disponíveis

### Ciclos Humanos

- [Ciclo 2026-07-03](cycles/2026-07-03/README.md)
- [Ciclo 2026-07-06](cycles/2026-07-06/README.md)
- [Ciclo 2026-07-13](cycles/2026-07-13/README.md)

### Ciclo Ativo em Preparação

- [Rascunho da Governança Semanal 2026-07-13](cycles/2026-07-13/2026-07-13-weekly-governance-draft.md)
- [Governança Semanal Operacional 2026-07-13](cycles/2026-07-13/2026-07-13-weekly-governance-operational.md)
- [Rascunho de Execucao por Evidencia 2026-07-13](cycles/2026-07-13/2026-07-13-maturity-evidence-execution-draft.md)
- [Run Sheet Datada `stg-2026-07-13-a`](cycles/2026-07-13/2026-07-13-first-combined-serious-window-run-sheet.md)
- [Bridge Quick-Fill `stg-2026-07-13-a`](cycles/2026-07-13/2026-07-13-staging-serious-window-bridge-quick-fill.md)
- [Go/No-Go Decision Packet `stg-2026-07-13-a`](cycles/2026-07-13/2026-07-13-staging-serious-window-go-no-go-decision-packet.md)
- [War Room `stg-2026-07-13-a`](cycles/2026-07-13/2026-07-13-staging-serious-window-war-room.md)
- [Tracking ao Vivo `stg-2026-07-13-a`](cycles/2026-07-13/2026-07-13-staging-serious-window-live-tracking.md)
- [Sign-Off `stg-2026-07-13-a`](cycles/2026-07-13/2026-07-13-staging-serious-window-signoff.md)

### Ciclo Fechado Mais Recente

- [Governança Semanal 2026-07-06](cycles/2026-07-06/2026-07-06-weekly-governance.md)
- [Preparação da Governança 2026-07-06](cycles/2026-07-06/2026-07-06-governance-meeting-prep.md)

### Janela Séria Datada `stg-2026-07-06-a`

- [War Room](cycles/2026-07-06/2026-07-06-staging-serious-window-war-room.md)
- [Tracking ao Vivo](cycles/2026-07-06/2026-07-06-staging-serious-window-live-tracking.md)
- [Folha de Preenchimento Manual](cycles/2026-07-06/2026-07-06-staging-serious-window-manual-fill-sheet.md)
- [Sign-Off](cycles/2026-07-06/2026-07-06-staging-serious-window-signoff.md)
- [Índice de Artefatos Gerados](generated/README.md)
- [Namespace da Janela `stg-2026-07-06-a`](generated/windows/stg-2026-07-06-a/README.md)

### Histórico Arquivado

- [Histórico Semanal](archive/weekly/README.md)
- [Tracking Histórico de Sprints](archive/sprint-tracking/README.md)
