package main

# =============================================================================
# M10 Sprint 10 — Policy Conftest Rego #2
# deny_ubuntu_latest_on_heavy_jobs: NÃO permitir runs-on: ubuntu-latest (string)
# em jobs PESADOS que Sprint 7 M4 definiu que RODAM APENAS EM SELF-HOSTED
# runners (pytest 7 serviços paralelo, E2E Playwright shard=8,
# nightly explorers live 50min+). Economia ~ 40-50min/mês GH Actions minutos
# e evita timeout de 6h GHA hard em jobs longos.
#
# Jobs pesados DEVEM usar runs-on como ARRAY de labels self-hosted:
#   runs-on: [self-hosted, ontrackchain-ci-e2e-ubuntu-latest, ontrackchain, linux, x64]
# =============================================================================

jobs_pesados_nome_contem_patterns := [
  "pytest-matrix-services",
  "pytest service:",
  "e2e-playwright",
  "run-explorers-live",
]

eh_job_pesado(job_name) {
  pat := jobs_pesados_nome_contem_patterns[_]
  contains(job_name, pat)
}

deny[msg] {
  some job_name
  j := input.jobs[job_name]
  eh_job_pesado(job_name)
  runs_on := object.get(j, "runs-on", null)
  # runs-on é exatamente a STRING "ubuntu-latest" → erro (deveria ser array self-hosted)
  runs_on == "ubuntu-latest"
  msg := sprintf(
    "M4 VIOLATION: job pesado '%s' usa runs-on: ubuntu-latest (string). Jobs pesados DEVEM usar runners self-hosted. Trocar por: runs-on: [self-hosted, ontrackchain-ci-e2e-ubuntu-latest, ontrackchain, linux, x64]. (Sprint 7 M4)",
    [job_name]
  )
}
