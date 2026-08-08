package main

# =============================================================================
# M10 Sprint 10 — Policy Conftest Rego #3
# deny_missing_timeout_minutes: TODO job CI que roda em workflows YAML
# OBRIGATORIAMENTE define timeout-minutes.
#
# Motivo: limite hard padrão GitHub Actions = 360min (6h) por job. Sem
# timeout-minutes explícito, um job com loop infinito acidental (ex:
# polling sem break, retry exponential backoff com max-attempts: 999)
# CONSOME 6 HORAS DE MINUTOS GH Actions (~ $48 se runner hosted pago).
# =============================================================================

deny[msg] {
  some job_name
  j := input.jobs[job_name]
  not object.get(j, "timeout-minutes", null)
  msg := sprintf(
    "RESILIENCE VIOLATION: job '%s' NÃO TEM 'timeout-minutes' definido. Todo job CI deve ter timeout explícito (minutos int). Exemplo: timeout-minutes: 15 (Sprint 10 M10)",
    [job_name]
  )
}
