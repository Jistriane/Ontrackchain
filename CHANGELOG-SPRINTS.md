# CHANGELOG Sprints Ontrackchain — Metodologia FAIL-CLOSED

> **Compilado automaticamente do roadmap em `ontrackchain/pyproject.toml` linhas L170-L192 (SSOT).**
> 
> **Regra Geral de TODO Sprint (válida S28+29 → atual):**
> - Working Tree SEMPRE limpa antes do commit
> - 8/8 gates padrão FAIL-CLOSED SEMPRE PASS
> - Hard constraints HC-1..HC-4 0 violações (ver `CONTRIBUTING.md`)
> - NÃO há commits parciais ou com regressão
> - Cada sprint entrega: INV → DESIGN → IMPL → DOCS → VAL → COMMIT

---

## Tabela Resumo Geral (24 sprints)

| Sprint | Prioridade | Tema Principal | Arquivos aprox. | Impacto DevX |
|---|---|---|---:|---|
| S28+55 | P4 | Governança Hardening CONTRIBUTING + .gitignore | 4 | ⭐⭐⭐⭐ (SOP padronizado) |
| S28+54 | P4 | Makefile CI Conveniência (4 atalhos 1-comando gates) | 3 | ⭐⭐⭐⭐⭐ (8 gates em 1 comando) |
| S28+53 | P3 | Logging Estruturado 10/10 Apps FastAPI | 8 | ⭐⭐⭐⭐ (observabilidade total) |
| S28+52 | P4 | Compose depends_on Healthy (13 relações) | 2–3 | ⭐⭐⭐⭐ (elimina race conditions e2e) |
| S28+51 | P4 | Makefile Compose Conveniência (5 targets) | 3 | ⭐⭐⭐ (scan-secrets, e2e-light, compose-X) |
| S28+50 | P3 | Docker Otimizado 11 Dockerfiles (non-root + HC) | 13 | ⭐⭐⭐⭐⭐ (segurança + cache layers + healthz) |
| S28+49 | P4 | Makefile Extras (format / audit / clean) | 1+docs | ⭐⭐⭐ (conveniência dev básica) |
| S28+48 | P4 | Logging Estruturado JSON (3 P0 + shared util) | ~6 | ⭐⭐⭐⭐ (fundação observabilidade) |
| S28+47 | P3 | SonarCloud QG Sync + CodeCov + Bandit SARIF | ~6 | ⭐⭐⭐ (qualidade + segurança estática) |
| S28+46 | P2 | mypy GLOBAL DEFAULT strict (9 flags) | 1 (pyproject) | ⭐⭐⭐⭐⭐ (FECHAMENTO CICLO STRICT) |
| S28+45 | P2 | app mock-oidc + 🏁 12 módulos strict | 1 app + pyproject | ⭐⭐⭐⭐ (último app strict) |
| S28+44 | P2 | app ai-service (último app real + LLM framework) | 1 app ~8 arquivos | ⭐⭐⭐⭐ (LLM + agents 2629 LOC) |
| S28+43 | P2 | app report-api (relatórios PDF / dashboards) | 1 app main 2737 LOC | ⭐⭐⭐ |
| S28+42 | P2 | app public-api (886 LOC endpoints sem RBAC) | 1 app | ⭐⭐ |
| S28+41 | P2 | app monitoring-api (SLO + healthz) | 1 app 2699 LOC | ⭐⭐⭐ |
| S28+40 | P2 | app investigation-api (8485 LOC + billing + intel) | 1 app 12 arquivos | ⭐⭐⭐⭐ |
| S28+39 | P2 | app case-management (CRUD casos) | 1 app 1353 LOC | ⭐⭐⭐ |
| S28+38 | P2 | app compliance-api (structural_screens + risk) | 1 app 6420 LOC 28 arqs. | ⭐⭐⭐⭐ |
| S28+37 | P2 | app auth-service (OIDC 2FA HMAC secrets) | 1 app ~primeiro app | ⭐⭐⭐⭐⭐ |
| S28+33 | P1 | package agents (sanctions/travel/rule 2629 LOC) | 1 pacote | ⭐⭐⭐⭐⭐ (core IA/agents) |
| S28+32 | P1 | package qa-gateway (9 CLI + policies + RLS guard) | 1 pacote | ⭐⭐⭐⭐⭐ (core governança qualidade) |
| S28+31 | P1 | package shared (SSOT logging/RBAC/helpers) | 1 pacote | ⭐⭐⭐⭐⭐ (SSOT fonte da verdade) |
| S28+30 | P0 | Fundação Monorepo (estrutura + pyproject base) | ~estrutura | 🏗️ fundação |
| S28+29 | P0 | Fundação Repositório + Governança M5 (SIGNOFF) | ~estrutura | 🏗️ fundação |

---

## Detalhe por Sprint (mais recente → mais antigo)

### 🏆 S28+55 — Governança Hardening CONTRIBUTING + .gitignore (P4)
**Objetivo**: Eliminar ambiguidade de contribuição e bloquear commits acidentais de segredos/relatórios.
- **Entregas**: `CONTRIBUTING.md` NOVO (6 seções: HC-1..HC-4, ciclo sprint 5 passos, tabela 8 gates, estrutura monorepo, padrão mensagem commit, checklist pré-commit 6 itens). `.gitignore` reorganizado 8 blocos comentados (segredos `.env.bak`/`.env.local`, tmp_qa/tmp_audit raiz+subdir, venv, compose.override.yml, caches hatch/coverage).
- **Arquivos**: 4 (CONTRIBUTING.md novo + .gitignore + README link + pyproject roadmap)
- **Impacto**: 0 chance de dev novo violar hard constraints sem ler. Checklist pré-commit 6 itens.

### ⚡ S28+54 — Makefile CI Conveniência 4 atalhos 1-comando (P4)
**Objetivo**: Encapsular 8 gates FAIL-CLOSED em atalhos 1-comando para reduzir curva de aprendizado dev novo.
- **Entregas**: 4 targets NÃO-gating em `/Makefile` raiz:
  1. `make ci-validate` (<10s): G1 M5 + G3 shell + G4 healthz + G8 settings
  2. `make ci-local` (~40s, **recomendado ANTES commit**): 8/8 gates padrão FAIL-CLOSED
  3. `make ci-pre-merge` (~120s, **recomendado PR/push**): 8 gates + lint + 6 testes unitários shared
  4. `make ci-smoke` (rápido): qa-gateway-smoke CLI
  - `.PHONY` atualizado (4 novos). Bloco help 6 linhas novas (TAB ASCII 0x09 validados). 4 targets body fim arquivo (44 linhas, TAB ASCII 0x09 100%).
- **Arquivos**: 3 (Makefile raiz + README Utilitários 4 novos bullets + pyproject roadmap)

### 📊 S28+53 — Logging Estruturado 10/10 Apps FastAPI (P3)
**Objetivo**: Completar cobertura total de logging estruturado JSON Lines + X-Request-Id middleware em TODOS serviços.
- **Entregas**: 6 apps FastAPI restantes habilitados com bloco padrão S28+48: compliance-api, investigation-api, monitoring-api, report-api, ai-service, mock-oidc. Total 3 P0 + 6 P3 = 10/10 serviços FastAPI. Padrão: `try/except` import `logging_util` ANTES `class Settings(BaseSettings)`, chamada `setup_structured_logging("service-name")`, `app.add_middleware(RequestIdLogMiddleware)` IMEDIATAMENTE após `app = FastAPI(...)` (depth calculation por linha inteira `L.count('(') - L.count(')')` robusto para kwargs multi-linha).
- **Arquivos**: 8 (6 mains FastAPI + pyproject roadmap + README Observabilidade 3→10 apps)
- **Validação crítica**: `ast.parse` 6/6 mains PASS (sandbox proíbe `py_compile` — regra S28+48 legado).

### 🩺 S28+52 — Compose depends_on Healthy 13 relações (P4)
**Objetivo**: Aproveitar HEALTHCHECKs dos Dockerfiles S28+50 e eliminar race conditions de startup em `e2e-light`.
- **Entregas**: 13 upgrades `service_started → service_healthy`:
  - CAT A (8 relações formato DICT existente): redis HC compose, 4 apps HC Dockerfile (investigation/compliance/monitoring/ai), case depende de ai.
  - CAT B (5 relações LIST → DICT conversão explícita): prometheus depende 4 apps + alertmanager; grafana depende prometheus.
  - Resultado final compose: **15 service_healthy / 10 service_completed_successfully / 2 service_started** (alertmanager/grafana 3rd-party sem HC = fail-safe `service_started` para não bloquear indefinidamente).
- **Arquivos**: 2–3 (docker-compose.yml + pyproject roadmap + README Containerização +2 bullets)

### 🛠️ S28+51 — Makefile Compose Conveniência 5 targets (P4)
**Objetivo**: Reduzir atrito de comandos longos compose/QA.
- **Entregas**: 5 targets NÃO-gating `/Makefile`:
  1. `scan-secrets-strict` (alias curto qa-gateway TruffleHog --only-verified)
  2. `e2e-light` (wrapper `scripts/s28p27-run-e2e-light.sh` — 8 containers perfil LEVE ~60s)
  3. `compose-up-full` (21 services stack completa observabilidade+apps+workers)
  4. `compose-health` (tabela formatada compose ps health state)
  5. `compose-purge FORCE_PURGE=1` (⚠️ destrutivo: `down -v` apaga volumes. Default SEM variável = fail-safe exit 5, não apaga nada)
  - TAB ASCII 0x09 100% validado em help + body.
- **Arquivos**: 3 (Makefile + README Utilitários 5 bullets novos + pyproject roadmap)

### 🐳 S28+50 — Docker Otimizado 11 Dockerfiles (P3)
**Objetivo**: Segurança de container + performance de build + healthz zero dependências.
- **Entregas**: Padrão único aplicado em 11 Dockerfiles Python:
  1. single-stage, **non-root UID/GID 10001 appuser** (segurança, não roda root)
  2. `PYTHONDONTWRITEBYTECODE=1` + `PYTHONUNBUFFERED=1` (evita pyc, logs flush)
  3. `HEALTHCHECK` com `urllib.request` `/healthz` (zero dependências novas, `curl`/`wget` não instalados)
  4. Ordem COPY otimizada cache: shared → agents → pyproject → src (camadas mutáveis por último)
  5. Remoção extras `[dev]` em runtime de auth/case/investigation/ai (reduz tamanho imagem)
  6. `rm /tmp/ontrackchain-*` APÓS pip install (limpa caches de build)
  7. `CMD sh -c "exec uvicorn ..."` (PID 1 = python, funciona sinal SIGTERM)
  8. `docker-compose.yml` corrige 4/4 `build.context` (auth/public/case/mock).
- **Arquivos**: 13 (10 apps Dockerfiles + qa-gateway Dockerfile + compose + pyproject roadmap + README Docker)

### 🧹 S28+49 — Makefile Extras (format / audit / clean) (P4)
**Objetivo**: Padronizar comandos básicos de qualidade sem dependências extras.
- **Entregas**: 3 targets NÃO-gating + conveniência:
  - `make format` → `ruff format hatch apps/ packages/ scripts/` (auto-fix seguro, não mexe AST/imports)
  - `make audit` → `pip-audit` 13 serviços, resumo HIGH/CRITICAL, logs por serviço `tmp_audit/` (CI bloqueia HIGH>0, local não bloqueia)
  - `make clean` → remove só `tmp_* __pycache__ .pytest_cache .mypy_cache **/*.pyc` (fail-safe: NÃO toca src/ git/ governança)
  - Padrão TAB ASCII 0x09 (fix legado: heredoc space = missing separator. Solução: Python literal `\t`).
- **Arquivos**: 1 (Makefile raiz) + docs opcionais.

### 📝 S28+48 — Logging Estruturado JSON (P0 auth/public/case) (P4)
**Objetivo**: Fundação de observabilidade stdlib sem 0 dependências novas.
- **Entregas**: Novo shared util `ontrackchain_shared/logging_util.py`: `json.dumps` + `logging.Formatter` + `contextvars` + middleware Starlette/FastAPI `RequestIdLogMiddleware` (X-Request-Id propagação). Habilitado em 3 P0: auth-service, public-api, case-management. Setup idempotente ANTES `class Settings`, bloco `try/except import tardio` (não quebra import se shared não instalado).
- **Validação crítica sandbox**: NÃO usar `py_compile` (permission denied escrever pyc). Substituir por `ast.parse` pure-memory.
- **Arquivos**: ~6 (shared/logging_util.py novo + 3 mains P0 + pyproject + README Observabilidade)

### 🛡️ S28+47 — SonarCloud QG Sync + GH Code Scanning (P3)
**Objetivo**: Alinhar qualidade estática entre CI e SonarCloud + segurança Bandit.
- **Entregas**: SSOT paths `sonar-project.properties` ↔ `ci.yml` args ↔ `ROOTS coverage` 7→13 serviços cobertos. CodeCov wildcard multiplos paths. Bandit SARIF → GH Code Scanning (categoria distinta de Ruff SARIF S28+34). 1 arquivo subpasta OBSOLETO marcado.
- **Arquivos**: ~6 (properties, ci.yml, workflow sarif, pyproject opcional)

### 🚀 S28+46 — mypy DEFAULT [tool.mypy] strict GLOBAL (P2)
**Objetivo**: 🏁 FECHAMENTO CICLO STRICT INCREMENTAL! Novos módulos NASÇEM strict automaticamente.
- **Entregas**: 9 flags estritas no bloco `[tool.mypy]` DEFAULT. 12 overrides explícitos permanecem como defesa em profundidade (não remover overrides = defesa em profundidade para futuras quebras acidentais).
- **Ordem metodológica** (ADR adotada): Shared → QA → Agents → 9 Apps 1×1 → Global Default Strict.
- **Arquivos**: 1 (pyproject.toml default section).

*(Sprints S28+31..S28+45 = fundação pacotes + apps 1×1 strict incremental. Consulte `ontrackchain/pyproject.toml` linhas L170-L181 para descrição por sprint. S28+29/S28+30 = fundação repositório e governança M5 SIGNOFF.)*

---

## Legenda Prioridades
- **P0**: Crítico / bloqueia main branch.
- **P1**: Core sistema (shared/qa-gateway/agents — fundação 3 SSOT).
- **P2**: Apps / features funcionais obrigatórias.
- **P3**: Qualidade, segurança, observabilidade (menor urgência, alto impacto).
- **P4**: Conveniência DevX / Governança / Hardening (menor esforço × maior impacto backlog).

## Como Atualizar
Sempre edite PRIMEIRO `ontrackchain/pyproject.toml` L170+ (roadmap comentado — SSOT oficial). Depois espelhe manualmente aqui. O script de validação `settings-dry-run` NÃO valida este changelog, mas a disciplina ágil exige a dupla entrada.
