# ai-service

Serviço FastAPI responsável por IA explicativa (XAI), insights de casos, Graph Intelligence e THEMIS (Case Intelligence Agent), com trilha de auditoria (`audit_logs`) e evidência regulatória (`evidence_trail`).

## Portas e base path

- Porta padrão: `8005`
- Base path: `/api/v1/ai`

## Banco e RLS

O serviço usa Postgres com RLS habilitado. Toda operação precisa de `app.organization_id` setado na sessão (`set_config`) para passar por `check_rls_context()`.

Headers exigidos na API:

- `X-Org-Id` (obrigatório)
- `X-Role` (obrigatório)
- `X-User-Id` (opcional)

Migrações relevantes:

- `0017_case_management_ai_service.sql` (inclui `ai_analysis_results`)
- `0019_ai_service_jobs.sql` (inclui `ai_service_jobs`)

## Jobs assíncronos (worker separado)

Decisão baseline:

- `themis` e `law-enforcement-export` operam como job (retornam `202`)
- jobs são processados por um worker separado (processo), que consome `ai_service_jobs` com `FOR UPDATE SKIP LOCKED`

### Fluxo (themis/export)

1) Cliente chama:

- `POST /api/v1/ai/themis` → `202` com `job_id`
- `POST /api/v1/ai/law-enforcement-export` → `202` com `job_id`

2) Worker processa o job e atualiza status em `ai_service_jobs`.

3) Cliente acompanha:

- `GET /api/v1/ai/jobs/{job_id}`

4) Human gate:

- `law-enforcement-export`: sempre exige dupla aprovação (Compliance + Legal) antes de concluir
- `themis`: pode exigir gate dependendo do risco; quando exigir, aprovações são feitas via:
  - `POST /api/v1/ai/jobs/{job_id}/approve`

### Rodar o worker

O worker precisa de um `org-id` para setar o contexto de RLS.

```bash
python3 -m ai_service.worker --org-id <UUID_DA_ORG>
```

Alternativa via env:

```bash
export AI_WORKER_ORG_ID=<UUID_DA_ORG>
python3 -m ai_service.worker
```

Modo “uma iteração” (útil para debug):

```bash
python3 -m ai_service.worker --org-id <UUID_DA_ORG> --once
```

## Desenvolvimento local (fora do Docker)

No diretório do monorepo (onde existem `packages/shared` e `packages/agents`), com Python 3.11:

```bash
python3 -m pip install -U pip
python3 -m pip install -e "ontrackchain/apps/ai-service[dev,llm]"
```

Rodar API:

```bash
uvicorn ai_service.main:app --host 0.0.0.0 --port 8005
```

## Docker

Alternativa recomendada (stack completa): usar `ontrackchain/docker-compose.yml` e subir também o serviço `ai-worker` com `AI_WORKER_ORG_ID`.

Build:

```bash
docker build -f ontrackchain/apps/ai-service/Dockerfile -t ontrackchain-ai-service .
```

Rodar API:

```bash
docker run --rm -p 8005:8005 \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_USER=ontrackchain \
  -e POSTGRES_PASSWORD=ontrackchain \
  -e POSTGRES_DB=ontrackchain \
  ontrackchain-ai-service
```

Rodar worker (mesma imagem):

```bash
docker run --rm \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_USER=ontrackchain \
  -e POSTGRES_PASSWORD=ontrackchain \
  -e POSTGRES_DB=ontrackchain \
  ontrackchain-ai-service \
  python3 -m ai_service.worker --org-id <UUID_DA_ORG>
```

## Testes

O `pytest` está em `project.optional-dependencies.dev`. Se você rodar testes dentro do container, instale os extras `dev` primeiro:

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest apps/ai-service/tests/test_ai_service.py -q
```
