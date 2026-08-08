package main

import future.keywords.in

deny[msg] {
    # ============================================================
    # Policy 04 M16b — Sprint 13: OBRIGA observabilidade endpoints
    # TODO serviço FastAPI (apps/<nome>/src/<nome>/main.py) expõe:
    #   1. Rota HTTP "/healthz" liveness (200 {"status":"ok"})
    #   2. Rota HTTP "/metrics" readness / export Prometheus (prometheus_fastapi_instrumentator)
    # NÃO se aplica: apps/frontend/ (React, não FastAPI) nem packages/*/cli.py (QA Gateway)
    # Violador → DENY merge em main (enforce_admins=true, ninguém bypassa).
    # ============================================================
    input[workflow_name][job_id].runs-on  # trigger qualquer workflow carregado; nós varremos arquivos Python também via Python script no CI.
    some source_file, line_content
    source_file := input.source_files[_]
    endswith(source_file, "/main.py")
    contains(source_file, "apps/")
    not contains(source_file, "node_modules")
    contains(source_file, "/src/")
    # Detecção: contém FastAPI(...) = é serviço FastAPI
    contains(input.python_ast_sources[source_file], "FastAPI()")
    # Falta rota /healthz ou /metrics
    (
        not contains(input.python_ast_sources[source_file], '"/healthz"')
        ;
        not contains(input.python_ast_sources[source_file], '"/metrics"')
    )
    msg := sprintf(
        "Policy04 Observabilidade Obrigatória (Sprint 13 M16b): Arquivo %s declara FastAPI() mas FALTA rota /healthz E/OU /metrics. Adicione: @app.get('/healthz') + PrometheusFastAPIInstrumentator(app).instrument().expose(endpoint='/metrics'). (action: bloqueio merge)",
        [source_file]
    )
}
