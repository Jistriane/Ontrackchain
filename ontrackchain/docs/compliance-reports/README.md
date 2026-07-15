# Relatorios de Compliance (Gerados)

## Objetivo

Centralizar os relatorios de compliance gerados a partir das metricas de governanca.

## Regra de Namespace

- os relatorios sao gerados por automacao e nao devem ser editados manualmente
- este namespace existe para outputs em Markdown/JSON consumidos por revisao operacional e auditoria interna

## Geracao

Gerador canonical:

- `python scripts/generate_compliance_report.py`

Target padrao:

- `docs/compliance-reports/compliance-report.md`

Via Makefile, quando habilitado:

- `docs/compliance-reports/compliance-report-YYYY-MM-DD.md`

## Precedencia de Leitura

- para baseline viva e decisao executiva, use `docs/` e `docs/governance-weekly/cycles/`
- para metricas de gate, use `docs/governance-weekly/generated/gates/`
- para este namespace, trate como saida gerada de apoio, nao como fonte primaria de contrato
