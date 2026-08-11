.PHONY: help help-serious-window prepare-serious-window-dispatch preflight-serious-window-dispatch render-serious-window-dispatch-packet postprocess-serious-window postprocess-serious-window-dry-run run-serious-window-local run-serious-window-local-dry-run check-sanctions-sync-status check-eu-sanctions-window rerun-compliance-worker run-eu-sanctions-window run-eu-sanctions-window-local check-compliance-provider-runtime run-regulatory-readiness-bundle doctor lint test test-shared typecheck build-local pre-commit-install pre-commit-all gov-m5-verify gov-m5-unit-test shell-syntax healthz-bypass-test qa-gateway-smoke doctor-plus compose-config compose-up compose-down compose-ps compose-logs compose-logs-follow all-checks

WINDOW_ID ?= stg-2026-07-06-a
MODE ?= baseline
ENVIRONMENT_NAME ?= staging-serious
DISPATCH_PACKET_OUTPUT_FILE ?= ci-artifacts/serious-window-dispatch-packet-$(WINDOW_ID).md
PAYLOAD_FILE ?= ci-artifacts/prepare-staging-window-output.json
GOVERNANCE_WEEKLY_DIR ?= docs/governance-weekly
RUN_URL ?= pending
SIGNOFF_OUTPUT_FILE ?=
PRIVATE_ENV_FILE ?= .env.staging.private
LOCAL_RUN_URL ?= local://staging-serious/$(WINDOW_ID)

help:
	@echo "Targets disponiveis na raiz:"
	@echo "  make prepare-serious-window-dispatch [WINDOW_ID=stg-2026-07-06-a] [MODE=baseline] [ENVIRONMENT_NAME=staging-serious] [DISPATCH_PACKET_OUTPUT_FILE=...]"
	@echo "  make preflight-serious-window-dispatch [WINDOW_ID=stg-2026-07-06-a] [MODE=baseline] [ENVIRONMENT_NAME=staging-serious] [GOVERNANCE_WEEKLY_DIR=...]"
	@echo "  make render-serious-window-dispatch-packet [WINDOW_ID=stg-2026-07-06-a] [MODE=baseline] [ENVIRONMENT_NAME=staging-serious] [DISPATCH_PACKET_OUTPUT_FILE=...]"
	@echo "  make postprocess-serious-window RUN_URL=<github-actions-run-url> [PAYLOAD_FILE=...] [GOVERNANCE_WEEKLY_DIR=...] [SIGNOFF_OUTPUT_FILE=...]"
	@echo "  make run-serious-window-local [WINDOW_ID=...] [MODE=baseline] [PRIVATE_ENV_FILE=.env.staging.private] [PAYLOAD_FILE=...] [GOVERNANCE_WEEKLY_DIR=...]"
	@echo "  make help-serious-window"
	@echo "  make postprocess-serious-window-dry-run RUN_URL=<github-actions-run-url> [PAYLOAD_FILE=...] [GOVERNANCE_WEEKLY_DIR=...] [SIGNOFF_OUTPUT_FILE=...]"
	@echo "  make run-serious-window-local-dry-run [WINDOW_ID=...] [MODE=baseline] [PRIVATE_ENV_FILE=.env.staging.private] [PAYLOAD_FILE=...] [GOVERNANCE_WEEKLY_DIR=...]"
	@echo "  make check-sanctions-sync-status"
	@echo "  make check-eu-sanctions-window"
	@echo "  make rerun-compliance-worker"
	@echo "  make run-eu-sanctions-window [WINDOW_ID=...] [PRIVATE_ENV_FILE=...] [CHECKS_DIR=...]"
	@echo "  make run-eu-sanctions-window-local [WINDOW_ID=...] [PRIVATE_ENV_FILE=...] [CHECKS_DIR=...]"
	@echo "  make check-compliance-provider-runtime [INTERNAL_BASE_URL=...] [PUBLIC_BASE_URL=...]"
	@echo "  make run-regulatory-readiness-bundle [WINDOW_ID=...] [PRIVATE_ENV_FILE=...] [CHECKS_DIR=...] [INTERNAL_BASE_URL=...] [PUBLIC_BASE_URL=...]"

help-serious-window:
	$(MAKE) -C ontrackchain help-serious-window

prepare-serious-window-dispatch:
	$(MAKE) -C ontrackchain prepare-serious-window-dispatch \
		WINDOW_ID="$(WINDOW_ID)" \
		MODE="$(MODE)" \
		ENVIRONMENT_NAME="$(ENVIRONMENT_NAME)" \
		GOVERNANCE_WEEKLY_DIR="$(GOVERNANCE_WEEKLY_DIR)" \
		DISPATCH_PACKET_OUTPUT_FILE="$(DISPATCH_PACKET_OUTPUT_FILE)"

preflight-serious-window-dispatch:
	$(MAKE) -C ontrackchain preflight-serious-window-dispatch \
		WINDOW_ID="$(WINDOW_ID)" \
		MODE="$(MODE)" \
		ENVIRONMENT_NAME="$(ENVIRONMENT_NAME)" \
		GOVERNANCE_WEEKLY_DIR="$(GOVERNANCE_WEEKLY_DIR)"

render-serious-window-dispatch-packet:
	$(MAKE) -C ontrackchain render-serious-window-dispatch-packet \
		WINDOW_ID="$(WINDOW_ID)" \
		MODE="$(MODE)" \
		ENVIRONMENT_NAME="$(ENVIRONMENT_NAME)" \
		GOVERNANCE_WEEKLY_DIR="$(GOVERNANCE_WEEKLY_DIR)" \
		DISPATCH_PACKET_OUTPUT_FILE="$(DISPATCH_PACKET_OUTPUT_FILE)"

postprocess-serious-window:
	$(MAKE) -C ontrackchain postprocess-serious-window \
		PAYLOAD_FILE="$(PAYLOAD_FILE)" \
		GOVERNANCE_WEEKLY_DIR="$(GOVERNANCE_WEEKLY_DIR)" \
		RUN_URL="$(RUN_URL)" \
		SIGNOFF_OUTPUT_FILE="$(SIGNOFF_OUTPUT_FILE)"

postprocess-serious-window-dry-run:
	$(MAKE) -C ontrackchain postprocess-serious-window-dry-run \
		PAYLOAD_FILE="$(PAYLOAD_FILE)" \
		GOVERNANCE_WEEKLY_DIR="$(GOVERNANCE_WEEKLY_DIR)" \
		RUN_URL="$(RUN_URL)" \
		SIGNOFF_OUTPUT_FILE="$(SIGNOFF_OUTPUT_FILE)"

run-serious-window-local:
	$(MAKE) -C ontrackchain run-serious-window-local \
		WINDOW_ID="$(WINDOW_ID)" \
		MODE="$(MODE)" \
		PRIVATE_ENV_FILE="$(PRIVATE_ENV_FILE)" \
		PAYLOAD_FILE="$(PAYLOAD_FILE)" \
		GOVERNANCE_WEEKLY_DIR="$(GOVERNANCE_WEEKLY_DIR)" \
		LOCAL_RUN_URL="$(LOCAL_RUN_URL)"

run-serious-window-local-dry-run:
	$(MAKE) -C ontrackchain run-serious-window-local-dry-run \
		WINDOW_ID="$(WINDOW_ID)" \
		MODE="$(MODE)" \
		PRIVATE_ENV_FILE="$(PRIVATE_ENV_FILE)" \
		PAYLOAD_FILE="$(PAYLOAD_FILE)" \
		GOVERNANCE_WEEKLY_DIR="$(GOVERNANCE_WEEKLY_DIR)" \
		LOCAL_RUN_URL="$(LOCAL_RUN_URL)"

check-sanctions-sync-status:
	$(MAKE) -C ontrackchain check-sanctions-sync-status

check-eu-sanctions-window:
	$(MAKE) -C ontrackchain check-eu-sanctions-window

rerun-compliance-worker:
	$(MAKE) -C ontrackchain rerun-compliance-worker

run-eu-sanctions-window:
	$(MAKE) -C ontrackchain run-eu-sanctions-window \
		WINDOW_ID="$(WINDOW_ID)" \
		PRIVATE_ENV_FILE="$(PRIVATE_ENV_FILE)" \
		CHECKS_DIR="$(CHECKS_DIR)"

run-eu-sanctions-window-local:
	$(MAKE) -C ontrackchain run-eu-sanctions-window-local \
		WINDOW_ID="$(WINDOW_ID)" \
		PRIVATE_ENV_FILE="$(PRIVATE_ENV_FILE)" \
		CHECKS_DIR="$(CHECKS_DIR)"

check-compliance-provider-runtime:
	$(MAKE) -C ontrackchain check-compliance-provider-runtime \
		INTERNAL_BASE_URL="$(INTERNAL_BASE_URL)" \
		PUBLIC_BASE_URL="$(PUBLIC_BASE_URL)"

run-regulatory-readiness-bundle:
	$(MAKE) -C ontrackchain run-regulatory-readiness-bundle \
		WINDOW_ID="$(WINDOW_ID)" \
		PRIVATE_ENV_FILE="$(PRIVATE_ENV_FILE)" \
		CHECKS_DIR="$(CHECKS_DIR)" \
		INTERNAL_BASE_URL="$(INTERNAL_BASE_URL)" \
		PUBLIC_BASE_URL="$(PUBLIC_BASE_URL)"

# ============================================================
# Sprint S28+22 — Targets Dev Friendly (backlog independente PGP)
# ============================================================
MONOREPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/ontrackchain

doctor:
	@echo "=== Ontrackchain Monorepo Doctor ==="
	@echo "Raiz do monorepo (ontrackchain/): $(MONOREPO_ROOT)"
	@echo -n "Python: " ; command -v python3 >/dev/null && python3 --version || echo "❌ python3 não encontrado"
	@echo -n "Hatch:  " ; command -v hatch >/dev/null && hatch --version || echo "⚠️  hatch não instalado (pyproject backend)"
	@echo -n "Git:    " ; command -v git >/dev/null && git --version || echo "❌ git não encontrado"
	@echo -n "Docker: " ; command -v docker >/dev/null && docker --version || echo "⚠️  docker não encontrado (build de imagens)"
	@echo -n "Arquivos SHA256 PASSO 0 M5: "
	@if [ -x "$(MONOREPO_ROOT)/scripts/gov-m5-verify-pre-sign.sh" ]; then \
	  cd "$(MONOREPO_ROOT)/.." && ./ontrackchain/scripts/gov-m5-verify-pre-sign.sh >/dev/null 2>&1 && echo "✅ OK" || echo "❌ FAIL (rode ./ontrackchain/scripts/gov-m5-verify-pre-sign.sh p/ detalhes)" ; \
	else echo "⚠️  script gov-m5-verify-pre-sign.sh ausente"; fi
	@echo "=== Use: make all-checks (13 gates FAIL-FAST, ADR-029) → doctor → typecheck (4-camadas fallback Strict Shared First) → build-local → qa-gateway-4strict → lint → test-shared"

lint:
	@echo "=== Ruff check (lint + isort + style) em monorepo ontrackchain/ ==="
	cd "$(MONOREPO_ROOT)" && python3 -m ruff check --config pyproject.toml \
		apps/*/src packages/shared/src packages/qa-gateway/src packages/agents/src .

test:
	@echo "=== pytest monorepo completo (todos apps + packages) ==="
	cd "$(MONOREPO_ROOT)" && python3 -m pytest -c pyproject.toml \
		--ignore=apps/frontend/tests -q --tb=short

test-shared:
	@echo "=== pytest APENAS packages/shared/tests (Sprint S28+22 3 novos testes catalog/middleware_rls/regulatory) ==="
	cd "$(MONOREPO_ROOT)" && python3 -m pytest -c pyproject.toml packages/shared/tests -v --tb=short

# ============================================================
# Sprint S28+28.2B / S28+31 P3: typecheck EXPANDIDO 8 apps + 3 packages
# Ordem: packages Shared First → qa → agents → apps alfabética
# REMOVIDO `| tail -30` = fail-closed sem truncamento de erro
# S28+31 NOVO: Strict Shared First via [[tool.mypy.overrides]] ontrackchain_shared.*
# EXECUÇÃO 4-CAMADAS (não depende PATH hatch/mypy instalado):
#   CAMADA 1) `mypy` entry-point no PATH (se usuário fez pip install mypy)
#   CAMADA 2) `python3 -m mypy` (se mypy instalado como módulo no venv atual)
#   CAMADA 3) `hatch -e default run mypy` (se hatch binário no PATH)
#   CAMADA 4) `python3 -m hatch -e default run mypy` (fallback módulo hatch)
# Se NENHUMA camada existe → instrução clara de como instalar.
# ============================================================
_MYPY_TARGETS = \
	packages/shared/src packages/qa-gateway/src packages/agents/src \
	apps/ai-service/src apps/auth-service/src apps/case-management/src \
	apps/compliance-api/src apps/investigation-api/src apps/monitoring-api/src \
	apps/public-api/src apps/report-api/src apps/mock-oidc/src

_MYPY_BASE = cd "$(MONOREPO_ROOT)" && \
	{ \
		if command -v mypy >/dev/null 2>&1; then \
			echo "  🧮 mypy camada 1/4 (PATH entry-point)"; \
			mypy --config-file pyproject.toml $(_MYPY_TARGETS); \
		elif python3 -m mypy --version >/dev/null 2>&1; then \
			echo "  🧮 mypy camada 2/4 (python3 -m mypy)"; \
			python3 -m mypy --config-file pyproject.toml $(_MYPY_TARGETS); \
		elif command -v hatch >/dev/null 2>&1; then \
			echo "  🧮 mypy camada 3/4 (hatch -e default run)"; \
			hatch -e default run mypy --config-file pyproject.toml $(_MYPY_TARGETS); \
		elif python3 -m hatch --version >/dev/null 2>&1; then \
			echo "  🧮 mypy camada 4/4 (python3 -m hatch -e default run mypy)"; \
			python3 -m hatch -e default run mypy --config-file pyproject.toml $(_MYPY_TARGETS); \
		else \
			echo "  ⚠️  mypy NÃO ENCONTRADO em NENHUMA das 4 camadas de fallback."; \
			echo "  ℹ️  Para habilitar typecheck STRICT Shared First (S28+31), instale UMA das opções:"; \
			echo "    a) pip install --user mypy>=1.10.0                                    (rápido, ~10MB)"; \
			echo "    b) (cd ontrackchain && python3 -m pip install -e '.[dev]')           (tudo, ~200MB)"; \
			echo "    c) pip install hatch && (cd ontrackchain && hatch env create default) (reproduz CI, ~400MB)"; \
			echo "  ℹ️  Configuração STRICT estrita do ontrackchain_shared.* já está ativa em pyproject.toml [tool.mypy.overrides]"; \
			echo "  ℹ️  (este make target NÃO quebra se mypy não existir — CI sempre tem hatch+mypy instalado)"; \
			exit 0; \
		fi; \
	}

typecheck:
	@echo "=== mypy STRICT Shared First (incremental, 8 apps + 3 packages) — Sprint S28+31 P3 ==="
	@echo "    (ontrackchain_shared.* = disallow_untyped_defs=true; outros packages/apps = baseline check_untyped_defs)"
	@$(_MYPY_BASE)

# ============================================================
# Sprint S28+28.2C: build-local FAIL-CLOSED (antes tinha || true)
# Apenas 3 packages buildáveis (não 9 apps FastAPI = Docker deploy)
# ============================================================
build-local:
	@echo "=== Hatch build: shared + qa-gateway + agents (FAIL-CLOSED sem || true) ==="
	cd "$(MONOREPO_ROOT)" && \
		(set -e; \
		hatch build packages/shared; \
		hatch build packages/qa-gateway; \
		hatch build packages/agents)
	@echo "Builds concluídos. Dist artifacts: $(MONOREPO_ROOT)/packages/*/dist/"
	@echo "  (não há build hatch para 9 apps FastAPI — deploy via Dockerfile diretamente)"

# ============================================================
# Sprint S28+26 — Targets P2 Dev + Governança (sem PGP clearsign)
# ============================================================
pre-commit-install:
	@echo "=== Instalar pre-commit framework + hooks locais (dev opt-in) ==="
	python3 -m pip install --user pre-commit || python3 -m pip install pre-commit
	pre-commit install --install-hooks
	@echo "Pronto. Rode 'make pre-commit-all' para validar MONOREPO inteiro."

pre-commit-all:
	@echo "=== Pre-commit RUN --ALL-FILES (Ruff + ShellCheck + merge-conflict + EOF + private-key) ==="
	pre-commit run --all-files || true
	@echo "Bandit (SAST) roda em stage=pre-push automaticamente. Rodar manual:"
	@echo "  pre-commit run bandit --hook-stage pre-push --all-files"

gov-m5-verify:
	@echo "=== PASSO 0 M5: Validação hash auto-referencial SIGNOFF-M5.md (awk NR<7 \|\| NR>11) ==="
	cd "$(MONOREPO_ROOT)/.." && ./ontrackchain/scripts/gov-m5-verify-pre-sign.sh

gov-m5-unit-test:
	@echo "=== Unit teste gov-m5 (2 cenários: hash OK + hash RUIM) — NÃO toca M5 real ==="
	cd "$(MONOREPO_ROOT)/.." && ./ontrackchain/scripts/s28p25-test-gov-m5-verify.sh

shell-syntax:
	@echo "=== bash -n syntax check EM TODOS scripts shell (20 scripts) — sem executar ==="
	cd "$(MONOREPO_ROOT)/.." && ./ontrackchain/scripts/s28p25-bash-syntax-check.sh

healthz-bypass-test:
	@echo "=== 18 testes bypass RBAC /healthz + /metrics × 9 serviços (AST grep, não inicia apps) ==="
	cd "$(MONOREPO_ROOT)/.." && ./ontrackchain/scripts/s28p24-check-healthz-metrics-bypass.sh

qa-gateway-smoke:
	@echo "=== QA Gateway smoke: 6 comandos --help (Sprint 13 M16b QA Gate L762) ==="
	cd "$(MONOREPO_ROOT)" && \
		for cmd in \
			"python3 -m ontrackchain_qa_gateway.policies.gate_01_serious_window --help" \
			"python3 -m ontrackchain_qa_gateway.policies.gate_02_aml_live_provider --help" \
			"python3 -m ontrackchain_qa_gateway.policies.gate_03_eu_sanctions_live --help" \
			"python3 -m ontrackchain_qa_gateway.policies.gate_04_regulatory_bundle --help" \
			"python3 -m ontrackchain_qa_gateway.policies.gate_05_compliance_provider --help" \
			"python3 -m ontrackchain_qa_gateway.migrations.apply_migrations --help"; do \
			echo "  🚀 $$cmd"; \
			eval $$cmd >/dev/null 2>&1 && echo "  ✅ OK" || echo "  ⚠️  N/A (ignorado — pode precisar pip install -e packages/qa-gateway[dev])"; \
		done

# ============================================================
# Sprint S28+30 P3: QA Gateway 4 STRICT scans OFFLINE / SEM banco
# Todos são --strict default=True, max_warnings=0 (fail-closed).
# Nenhum precisa de PG/Redis/Portas (todos code-scan AST ou files).
# Ordem FAIL-FAST: BW (billing-caps) → BE (billing-enf) → LR (lgpd ropd) → RBAC (maior)
#
# EXECUÇÃO 2-CAMADAS (independentemente de PATH / pip install -e):
#   CAMADA 1) se `qa-gateway` entry-point existe em PATH → usa direto
#   CAMADA 2) senão → PYTHONPATH=packages/qa-gateway/src python3 -m qa_gateway.cli
#              (não precisa de pip install; só precisa do pacote src/ existir no monorepo)
# ============================================================
_QA_GW_PY_ROOT = $(MONOREPO_ROOT)/packages/qa-gateway
_QA_RUN = if command -v qa-gateway >/dev/null 2>&1; then qa-gateway; else cd $(MONOREPO_ROOT) && PYTHONPATH=$(_QA_GW_PY_ROOT)/src:$$PYTHONPATH python3 -m qa_gateway.cli; fi

qa-gateway-scan-billing-capabilities-strict:
	@echo "🧾 QA-GATE Q3-05: scan-billing-capabilities --strict --max-warnings 0 (BW-001..004 fail-closed)"
	@mkdir -p $(MONOREPO_ROOT)/tmp_qa
	@$(_QA_RUN) scan-billing-capabilities \
		--project-root $(MONOREPO_ROOT) \
		--strict --max-warnings 0 \
		--failures-json $(MONOREPO_ROOT)/tmp_qa/billing-capabilities.failures.json

qa-gateway-scan-billing-enforcement-strict:
	@echo "🛡️  QA-GATE Q3-06: scan-billing-enforcement --strict --max-warnings 0 (BE-001..004 fail-closed)"
	@mkdir -p $(MONOREPO_ROOT)/tmp_qa
	@$(_QA_RUN) scan-billing-enforcement \
		--project-root $(MONOREPO_ROOT) \
		--strict --max-warnings 0 --skip-prod-redis \
		--failures-json $(MONOREPO_ROOT)/tmp_qa/billing-enforcement.failures.json

qa-gateway-scan-lgpd-ropd-strict:
	@echo "🪪  QA-GATE Q3-07: scan-lgpd-ropd --strict --max-warnings 0 (LR-001..005 + ROPD E001..E003)"
	@mkdir -p $(MONOREPO_ROOT)/tmp_qa
	@$(_QA_RUN) scan-lgpd-ropd \
		--project-root $(MONOREPO_ROOT) \
		--strict --max-warnings 0 \
		--failures-json $(MONOREPO_ROOT)/tmp_qa/lgpd-ropd.failures.json

qa-gateway-scan-rbac-strict:
	@echo "🚦 QA-GATE Q3-04: scan-rbac --strict (9 serviços, max-anonymous-write=0) — SEM --db-url (RBAC-W004 ignorado)"
	@mkdir -p $(MONOREPO_ROOT)/tmp_qa
	@$(_QA_RUN) scan-rbac \
		--project-root $(MONOREPO_ROOT) \
		--strict --max-warnings 0 --max-anonymous-write-per-service 0 \
		--failures-json $(MONOREPO_ROOT)/tmp_qa/rbac.failures.json

# Agregador dos 4 scans strict (usado pelo all-checks e manual)
qa-gateway-all-strict-ci:
	@mkdir -p "$(MONOREPO_ROOT)/tmp_qa"
	@echo "============================================================"
	@echo " Sprint S28+30 QA-Gateway ALL STRICT (4 gates offline) "
	@echo "============================================================"
	@$(MAKE) qa-gateway-scan-billing-capabilities-strict
	@echo ""
	@$(MAKE) qa-gateway-scan-billing-enforcement-strict
	@echo ""
	@$(MAKE) qa-gateway-scan-lgpd-ropd-strict
	@echo ""
	@$(MAKE) qa-gateway-scan-rbac-strict
	@echo ""
	@echo "✅ QA-Gateway STRICT CI (4/4) concluído. Relatórios JSON:"
	@echo "  - $(MONOREPO_ROOT)/tmp_qa/*.failures.json"

doctor-plus:
	@$(MAKE) doctor
	@echo
	@echo "=== Doctor Plus (P2 S28+26 → P3 S28+30) — gates locais rápidos ==="
	@echo -n "Pre-commit framework: "
	@command -v pre-commit >/dev/null 2>&1 && echo "✅ $(pre-commit --version 2>&1)" || echo "⚠️  NÃO instalado → rode: make pre-commit-install"
	@echo -n "QA Gateway import: "
	@cd "$(MONOREPO_ROOT)" && python3 -c "import ontrackchain_qa_gateway; print('✅', ontrackchain_qa_gateway.__name__)" 2>/dev/null || echo "⚠️  Não importável (pip install -e packages/qa-gateway[dev])"
	@echo -n "qa-gateway CLI PATH: "
	@command -v qa-gateway >/dev/null 2>&1 && echo "✅ $(command -v qa-gateway)" || echo "⚠️  NÃO em PATH (pip install -e packages/qa-gateway)"
	@echo
	@echo "Atalhos:"
	@echo "  make gov-m5-verify                     → PASSO 0 M5 hash auto-ref (S28+21)"
	@echo "  make gov-m5-unit-test                  → 2 cenários mock do gov-m5 (S28+25)"
	@echo "  make shell-syntax                      → bash -n 21 scripts (S28+25)"
	@echo "  make healthz-bypass-test               → 18 bypass RBAC × 9 serviços (S28+24)"
	@echo "  make qa-gateway-smoke                  → 6 comandos qa-gateway --help (M16b)"
	@echo "  make qa-gateway-all-strict-ci          → 4 STRICT scans Q3-04/05/06/07 (NOVO S28+30 P3)"
	@echo "  make pre-commit-all                    → ruff+shellcheck monorepo"
	@echo "  make all-checks                        → 13 gates FAIL-FAST (Sprint S28+30)"
	@echo "  make typecheck → make build-local → make qa-gateway-all-strict-ci → make lint → make test-shared (fluxo dev padrão)"

# ============================================================
# Sprint S28+27 — Docker Compose local + aggregator all-checks
# Arquivo: ontrackchain/docker-compose.yml (32 services + profiles keycloak)
# ============================================================
COMPOSE_FILE ?= $(MONOREPO_ROOT)/docker-compose.yml
COMPOSE_OVERLAY_OIDC ?= $(MONOREPO_ROOT)/docker-compose.oidc-local.yml
E2E_LIGHT_PROFILES ?= --profile mock-oidc

compose-config:
	@echo "=== Docker Compose: validar sintaxe (config -q) ==="
	docker compose -f "$(COMPOSE_FILE)" config -q >/dev/null 2>&1 && echo "✅ docker-compose.yml sintaxe OK (32 services declarados)" || (echo "❌ docker-compose.yml FALHOU sintaxe"; docker compose -f "$(COMPOSE_FILE)" config; exit 10)
	@echo "  Overlay OIDC local: $(COMPOSE_OVERLAY_OIDC)"
	@command -v docker >/dev/null 2>&1 && echo "  Docker client: OK ($(docker --version 2>&1))" || echo "  ⚠️ Docker não disponível"

compose-up:
	@echo "=== Docker Compose UP: perfil LEVE (traefik + pg + redis + bootstrap + auth + public + ai + mock-oidc) ==="
	docker compose -f "$(COMPOSE_FILE)" $(E2E_LIGHT_PROFILES) up -d \
		traefik postgres redis postgres-bootstrap auth-service public-api ai-service mock-oidc
	@echo "Containeres ativos:"
	@docker compose -f "$(COMPOSE_FILE)" ps --format '{{.Service}} → {{.State}}  {{.Health}}' 2>/dev/null | head -25 || true

compose-down:
	@echo "=== Docker Compose DOWN (mantém volumes. Use compose-purge para apagar volumes!) ==="
	docker compose -f "$(COMPOSE_FILE)" down --remove-orphans

compose-ps:
	@echo "=== Docker Compose PS (status containeres) ==="
	docker compose -f "$(COMPOSE_FILE)" ps --format 'table {{.Name}}\t{{.Service}}\t{{.State}}\t{{.Health}}\t{{.Ports}}'

compose-logs:
	@echo "=== Docker Compose logs (últimas 50 linhas por service LEVE) ==="
	docker compose -f "$(COMPOSE_FILE)" logs --tail=50 \
		traefik postgres redis auth-service public-api ai-service mock-oidc 2>&1 | tail -200

compose-logs-follow:
	@echo "=== Docker Compose logs -f (follow). Ctrl-C para parar. ==="
	docker compose -f "$(COMPOSE_FILE)" logs -f --tail=20 \
		traefik postgres redis auth-service public-api ai-service mock-oidc

# ============================================================
# Aggregator ALL-CHECKS (Sprint S28+30 P3): 13 gates FAIL-FAST
# Ordem ADR-029: baratos → médios → caros. FAIL em 1 aborta restante.
# GATES 1-7  (baratos, 0-2 min): doctor / M5 / shell / healthz / typecheck / build-local
# GATES 8-11 (médios,   1-3 min): qa-gateway 4 STRICT scans offline
# GATES 12-13 (caros,   2-5 min): ruff lint / test-shared pytest
# UPDATED S28+30: qa-gateway-4scans NOVOS entre build-local e lint (fail early estrutura)
# ============================================================
all-checks:
	@echo "============================================================"
	@echo " Sprint S28+30 ALL-CHECKS (13 gates locais, ~7 min total) "
	@echo "============================================================"
	@echo ""
	@$(MAKE) doctor
	@echo ""
	@$(MAKE) gov-m5-verify
	@echo ""
	@$(MAKE) gov-m5-unit-test
	@echo ""
	@$(MAKE) shell-syntax
	@echo ""
	@$(MAKE) healthz-bypass-test
	@echo ""
	@$(MAKE) typecheck
	@echo ""
	@$(MAKE) build-local
	@echo ""
	@$(MAKE) qa-gateway-all-strict-ci
	@echo ""
	@$(MAKE) lint
	@echo ""
	@$(MAKE) test-shared
	@echo ""
	@echo "============================================================"
	@echo " ✅ ALL-CHECKS PASSOU: 13 gates locais concluídos "
	@echo "============================================================"
	@echo "  Próximos passos opcionais:"
	@echo "    make qa-gateway-smoke compose-up"
	@echo "    ./ontrackchain/scripts/s28p27-run-e2e-light.sh"
