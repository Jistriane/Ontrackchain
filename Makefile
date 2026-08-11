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
	@echo "=== Use: make all-checks (9 gates) → doctor → typecheck → build-local → qa-gateway-smoke"

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
# Sprint S28+28.2B: typecheck EXPANDIDO 8 apps + 3 packages (antes 5/2)
# Ordem: packages Shared First → apps alfabética
# REMOVIDO `| tail -30` = fail-closed sem truncamento de erro
# ============================================================
typecheck:
	@echo "=== mypy check_untyped_defs incremental (8 apps + 3 packages) — Sprint S28+28 P2 ==="
	cd "$(MONOREPO_ROOT)" && python3 -m mypy --config-file pyproject.toml \
		packages/shared/src packages/qa-gateway/src packages/agents/src \
		apps/ai-service/src apps/auth-service/src apps/case-management/src \
		apps/compliance-api/src apps/investigation-api/src apps/monitoring-api/src \
		apps/public-api/src apps/report-api/src apps/mock-oidc/src

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

doctor-plus:
	@$(MAKE) doctor
	@echo
	@echo "=== Doctor Plus (P2 S28+26) — gates locais rápidos ==="
	@echo -n "Pre-commit framework: "
	@command -v pre-commit >/dev/null 2>&1 && echo "✅ $(pre-commit --version 2>&1)" || echo "⚠️  NÃO instalado → rode: make pre-commit-install"
	@echo -n "QA Gateway import: "
	@cd "$(MONOREPO_ROOT)" && python3 -c "import ontrackchain_qa_gateway; print('✅', ontrackchain_qa_gateway.__name__)" 2>/dev/null || echo "⚠️  Não importável (pip install -e packages/qa-gateway[dev])"
	@echo
	@echo "Atalhos:"
	@echo "  make gov-m5-verify           → PASSO 0 M5 hash auto-ref (S28+21)"
	@echo "  make gov-m5-unit-test        → 2 cenários mock do gov-m5 (S28+25)"
	@echo "  make shell-syntax            → bash -n 20 scripts (S28+25)"
	@echo "  make healthz-bypass-test     → 18 bypass RBAC × 9 serviços (S28+24)"
	@echo "  make qa-gateway-smoke        → 6 comandos qa-gateway --help (M16b)"
	@echo "  make pre-commit-all          → ruff+shellcheck monorepo"
	@echo "  make all-checks              → 9 gates FAIL-FAST (Sprint S28+28)"
	@echo "  make typecheck → make build-local → make lint → make test-shared (fluxo dev padrão)"

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
# Aggregator ALL-CHECKS (Sprint S28+28 P2): 9 gates locais FAIL-FAST
# Ordem: baratos → caros → falha se um falhar (set -e implícito via make)
# UPDATED 28+28: +typecheck (g8), +build-local (g9) ANTES de lint/test
# ============================================================
all-checks:
	@echo "============================================================"
	@echo " Sprint S28+28 ALL-CHECKS (9 gates locais, ~5 min) "
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
	@$(MAKE) lint
	@echo ""
	@$(MAKE) test-shared
	@echo ""
	@echo "============================================================"
	@echo " ✅ ALL-CHECKS PASSOU: 9 gates locais concluídos "
	@echo "============================================================"
	@echo "  Próximos passos opcionais:"
	@echo "    make qa-gateway-smoke compose-up"
	@echo "    ./ontrackchain/scripts/s28p27-run-e2e-light.sh"
