package main

# =============================================================================
# M10 Sprint 10 — Policy Conftest Rego #1
# deny_continue_on_error_p0_gate: NUNCA permitir continue-on-error=true
# em jobs que são GATES CRÍTICOS P0/P1 (RLS, OIDC, QA Gateway, SAST Bandit,
# pip-audit, Guard anti-hardcoded tokens, Sonar Quality Gate).
#
# Se alguém abrir um PR tentando transformar um gate P0 em NÃO-BLOQUEANTE
# (porque "está dando muito false positive"), a policy nega o merge ANTES
# do código entrar em main.
# =============================================================================

criticos_gate_nome_contem_patterns := [
  "gate-p0",
  "QA Gate",
  "SAST:",
  "Dep Audit:",
  "Guard:",
  "Quality Gate",
  "Policy Gate:",
  "secrets-guard-skeleton",
]

tem_nome_gate_critico(job_name) {
  pat := criticos_gate_nome_contem_patterns[_]
  contains(job_name, pat)
}

deny[msg] {
  some job_name
  j := input.jobs[job_name]
  tem_nome_gate_critico(job_name)
  object.get(j, "continue-on-error", false) == true
  msg := sprintf(
    "P0 VIOLATION: job '%s' é gate CRÍTICO e tem continue-on-error=true. Gates P0 DEVEM SER BLOQUEANTES (continue-on-error=false).",
    [job_name]
  )
}
