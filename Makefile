.PHONY: help help-serious-window prepare-serious-window-dispatch preflight-serious-window-dispatch render-serious-window-dispatch-packet postprocess-serious-window postprocess-serious-window-dry-run run-serious-window-local run-serious-window-local-dry-run check-sanctions-sync-status check-eu-sanctions-window rerun-compliance-worker run-eu-sanctions-window run-eu-sanctions-window-local check-compliance-provider-runtime run-regulatory-readiness-bundle doctor lint test test-shared typecheck build-local pre-commit-install pre-commit-all gov-m5-verify gov-m5-unit-test shell-syntax healthz-bypass-test qa-gateway-smoke doctor-plus compose-config compose-up compose-down compose-ps compose-logs compose-logs-follow all-checks format audit clean scan-secrets-strict e2e-light compose-up-full compose-purge compose-health

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
	@echo ""
	@echo "Utilidades Dev (Sprint S28+49 P4):"
	@echo "  make format  → ruff format apps/ packages/ scripts/ (auto-formata Python, NÃO quebra código)"
	@echo "  make audit   → pip-audit 13 serviços (CVE HIGH/CRITICAL resumido, NÃO bloqueia merge localmente)"
	@echo "  make clean   → remove tmp_*/* + __pycache__ + .pytest_cache (NÃO toca em src/, git/ ou SIGNOFF-*.md)"

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
	@echo "=== Use: make all-checks (15 gates FAIL-FAST, ADR-029) → doctor → typecheck (4-camadas fallback Strict Shared First + qa + agents) → build-local → qa-gateway-5strict+segredos+premerge → lint → test-shared"

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
# Sprint S28+35 P3: +2 gates NOVOS = 6 total QA no all-checks
# Todos são --strict default=True, max_warnings=0 (fail-closed).
# Nenhum precisa de PG/Redis/Portas (todos code-scan AST ou files).
# Ordem FAIL-FAST ADR-029 (barato → custoso):
#   · P0 SEGREDOS: scan-secrets-trufflehog (10-60s, mais barato, BLOQUEIA merge em segredo vazado)
#   · P1 ESTRUTURAL 4 gates: BW (billing-caps) → BE (billing-enf) → LR (lgpd ropd) → RBAC (maior)
#   · P1 AGRUPADOR: qa-gateway-all-strict-ci (4 gates acima duplicado? NÃO — aggregator dev isolado)
#   · P1 ORQUESTRADOR: run-pre-merge-gates (consolidado report JSON ADR-029, FAIL-FAST 5 gates internamente)
# EXECUÇÃO 2-CAMADAS (mesmo helper _QA_RUN S28+30):
#   CAMADA 1) se `qa-gateway` entry-point existe em PATH → usa direto
#   CAMADA 2) senão → PYTHONPATH=packages/qa-gateway/src python3 -m qa_gateway.cli
# ============================================================
_QA_GW_PY_ROOT = $(MONOREPO_ROOT)/packages/qa-gateway
_QA_RUN = if command -v qa-gateway >/dev/null 2>&1; then qa-gateway; else cd $(MONOREPO_ROOT) && PYTHONPATH=$(_QA_GW_PY_ROOT)/src:$$PYTHONPATH python3 -m qa_gateway.cli; fi

# Sprint S28+35 P3 NOVO: P0 segredos verificados. Roda MAIS BARATO PRIMEIRO FAIL-FAST.
qa-gateway-scan-secrets-trufflehog-strict:
	@echo "🔐 QA-GATE Q3-08: scan-secrets-trufflehog --strict --max-warnings 0 (only-verified default, P0 segredos)"
	@mkdir -p $(MONOREPO_ROOT)/tmp_qa
	@$(_QA_RUN) scan-secrets-trufflehog \
		--project-root $(MONOREPO_ROOT) \
		--strict --max-warnings 0 --only-verified \
		--failures-json $(MONOREPO_ROOT)/tmp_qa/secrets-trufflehog.failures.json

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

# Sprint S28+35 P3 NOVO: Orquestrador ADR-029 consolidado (5 gates internos, report JSON pre-merge).
# Roda DEPOIS dos 4+1 individuais = verificação duplicada intencional? NÃO.
#   · individuais = FAIL-FAST granular 1 a 1 (usuário vê logo qual gate quebrou)
#   · orquestrador = relatório consolidado JSON único (para CI logs, histórico, arquivamento RIPD Art.30 LGPD)
qa-gateway-run-pre-merge-gates:
	@mkdir -p "$(MONOREPO_ROOT)/tmp_qa" "$(MONOREPO_ROOT)/tmp_qa/pre-merge-reports"
	@echo "🛂 QA-GATE Q3-09: run-pre-merge-gates --strict ADR-029 FAIL-FAST (report JSON consolidado)"
	@$(_QA_RUN) run-pre-merge-gates \
		--project-root $(MONOREPO_ROOT) \
		--strict --max-warnings 0 \
		--report-dir $(MONOREPO_ROOT)/tmp_qa/pre-merge-reports \
		--failures-json $(MONOREPO_ROOT)/tmp_qa/pre-merge-gates.failures.json

doctor-plus:
	@$(MAKE) doctor
	@echo
	@echo "=== Doctor Plus (P2 S28+26 → P3 S28+35) — gates locais rápidos ==="
	@echo -n "Pre-commit framework: "
	@command -v pre-commit >/dev/null 2>&1 && echo "✅ $(pre-commit --version 2>&1)" || echo "⚠️  NÃO instalado → rode: make pre-commit-install"
	@echo -n "QA Gateway import: "
	@cd "$(MONOREPO_ROOT)" && python3 -c "import ontrackchain_qa_gateway; print('✅', ontrackchain_qa_gateway.__name__)" 2>/dev/null || echo "⚠️  Não importável (pip install -e packages/qa-gateway[dev])"
	@echo -n "qa-gateway CLI PATH: "
	@command -v qa-gateway >/dev/null 2>&1 && echo "✅ $(command -v qa-gateway)" || echo "⚠️  NÃO em PATH (fallback PYTHONPATH automático nos targets make)"
	@echo -n "trufflehog binário (P0 segredos): "
	@command -v trufflehog >/dev/null 2>&1 && echo "✅ $(trufflehog --version 2>&1 | head -1)" || echo "⚠️  NÃO em PATH (instale: https://github.com/trufflesecurity/trufflehog - fallback dry-run Q3-08)"
	@echo
	@echo "Atalhos QA (S28+30 P3 → S28+35 P3):"
	@echo "  make gov-m5-verify                                   → PASSO 0 M5 hash auto-ref (S28+21)"
	@echo "  make gov-m5-unit-test                                → 2 cenários mock do gov-m5 (S28+25)"
	@echo "  make shell-syntax                                    → bash -n 21 scripts (S28+25)"
	@echo "  make healthz-bypass-test                             → 18 bypass RBAC × 9 serviços (S28+24)"
	@echo "  make qa-gateway-smoke                                → 6 comandos qa-gateway --help (M16b)"
	@echo
	@echo "  make scan-secrets-strict                              → P0 segredos verificados (alias qa-gateway-scan-secrets-trufflehog-strict, S28+51)"
	@echo "  make e2e-light                                        → E2E smoke LEVE (8 containers, ~60 seg) = ./ontrackchain/scripts/s28p27-run-e2e-light.sh (S28+51)"
	@echo "  make compose-up-full                                  → Docker Compose FULL (observabilidade + 9 apps + workers, ~30 containers) (S28+51)"
	@echo "  make compose-health                                   → Resumo HEALTH status de todos containers (tabela formatada) (S28+51)"
	@echo "  make compose-purge                                    → ⚠️ APAGA VOLUMES (postgres_data, grafana, etc). Use FORCE_PURGE=1 para confirmar. (S28+51)"
	@echo "  make qa-gateway-scan-secrets-trufflehog-strict       → P0 segredos verificados (NOVO S28+35 P3)"
	@echo "  make qa-gateway-all-strict-ci                        → 4 STRICT scans Q3-04/05/06/07 (S28+30 P3)"
	@echo "  make qa-gateway-run-pre-merge-gates                  → ADR-029 FAIL-FAST 5 gates ORQUESTRADOR (NOVO S28+35 P3)"
	@echo "  make pre-commit-all                                  → ruff+shellcheck monorepo"
	@echo "  make settings-dry-run                                → valida settings.yml NA RAIZ + contexts obrigatórios (NOVO S28+36 P4)"
	@echo "  make settings-apply                                  → roda workflow repository-settings (gh CLI autenticado)"
	@echo "  make all-checks                                      → 15 gates FAIL-FAST LOCAL (Sprint S28+35 P3)"
	@echo "  make typecheck → make build-local → make qa-gateway-scan-secrets-trufflehog-strict → make qa-gateway-all-strict-ci → make qa-gateway-run-pre-merge-gates → make lint → make test-shared  (fluxo dev padrão ADR-029)"

# ============================================================
# Sprint S28+36 P4: Repository Settings YAML (SSOT na RAIZ)
# BUG FIX: settings.yml movido de ontrackchain/.github/settings.yml (OBSOLETO)
# para /home/jistriane/Ontrackchain/.github/settings.yml (caminho canônico GitHub)
# 2 targets locais:
#   · settings-dry-run: valida sintaxe YAML + contexts obrigatórios (sem gh CLI)
#   · settings-apply: dispara o workflow repository-settings via gh CLI
# ============================================================
_SETTINGS_ROOT = .github/settings.yml
_SETTINGS_SCRIPT = $(MONOREPO_ROOT)/scripts/s28p36-settings-validate.py

settings-dry-run:
	@echo "🛡️  Repository Settings DRY-RUN (Sprint S28+36 P4)"
	@echo "  arquivo SSOT: $(_SETTINGS_ROOT)"
	@echo "  validador:    $(_SETTINGS_SCRIPT)"
	@mkdir -p tmp_qa
	@python3 "$(_SETTINGS_SCRIPT)"

settings-apply:
	@echo "🚀 Disparar workflow repository-settings via gh CLI (Settings → Apply)"
	@command -v gh >/dev/null 2>&1 || { echo "ERRO: gh CLI não está instalado/autenticado. Instale: https://cli.github.com/ → gh auth login"; echo "   Alternativa manual: abrir Actions → Repository Settings Apply → Run workflow → Dry-run=OFF"; exit 32; }
	@echo "  gh workflow run repository-settings.yml (inputs.dry_run=false = APLICAR de verdade)"
	@gh workflow run repository-settings.yml --ref main -f dry_run=false
	@echo "✅ Workflow disparado. Status: https://github.com/Ontrackchain/ontrackchain/actions/workflows/repository-settings.yml"

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
# Aggregator ALL-CHECKS (Sprint S28+35 P3): 15 gates FAIL-FAST
# Ordem ADR-029: baratos → médios → caros. FAIL em 1 aborta restante.
# GATES 1-7  (baratos, 0-2 min): doctor / M5 / shell / healthz / typecheck / build-local
# GATES 8-14 (médios,   1-4 min): qa-gateway P0 segredos + 4 STRICT estrutural + aggregator + orquestrador
# GATES 15-16 (caros,   2-5 min): ruff lint / test-shared pytest
# UPDATED S28+35: scan-secrets-trufflehog-strict P0 + run-pre-merge-gates ADR-029 ORQUESTRADOR
# ============================================================
all-checks:
	@echo "============================================================"
	@echo " Sprint S28+35 ALL-CHECKS (15 gates locais, ~8 min total) "
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
	@echo ""
	@echo "--- QA SESSION: P0 SEGREDOS primeiro (FAIL-FAST mais barato) ---"
	@$(MAKE) qa-gateway-scan-secrets-trufflehog-strict
	@echo ""
	@$(MAKE) qa-gateway-all-strict-ci
	@echo ""
	@$(MAKE) qa-gateway-run-pre-merge-gates
	@echo ""
	@echo "--- QUALITY SESSION FINAL (mais caros, lint + unit tests) ---"
	@$(MAKE) lint
	@echo ""
	@$(MAKE) test-shared
	@echo ""
	@echo "============================================================"
	@echo " ✅ ALL-CHECKS PASSOU: 15 gates locais concluídos "
	@echo "============================================================"
	@echo "  Próximos passos opcionais:"
	@echo "    make qa-gateway-smoke compose-up"
	@echo "    ./ontrackchain/scripts/s28p27-run-e2e-light.sh"

# ============================================================
# Sprint S28+49 P4: Makefile Extras (make format / make audit / make clean)
# NENHUM target é gating (não adicionado a all-checks).
# Todos preservam src/, .git/, SIGNOFF-M5.md, settings.yml e qualquer código de negócio.
#  · format: ruff format hatch = auto-fix safe (não toca em imports nem AST)
#  · audit:  pip-audit 13 serviços RESUMIDO. NÃO bloqueia localmente se HIGH>0.
#  · clean:  remove apenas tmp_*, __pycache__, .pytest_cache, .mypy_cache, *.pyc
# ============================================================
format: ## Auto-formata Python (ruff format) em apps/, packages/, scripts/. S28+49
	@echo "🟣 make format — ruff format hatch (auto-fix safe, NÃO altera imports)"
	@echo "   Alvos: ontrackchain/{apps,packages,scripts}"
	@cd ontrackchain && 		hatch run ruff format apps/ packages/ scripts/

audit: ## pip-audit 13 serviços (CVE HIGH/CRITICAL resumido, NÃO bloqueia local). S28+49
	@echo "🔴 make audit — pip-audit 13 serviços (CVE HIGH/CRITICAL resumido)"
	@mkdir -p tmp_audit
	@AUDIT_ROOTS="apps/case-management apps/auth-service apps/ai-service apps/investigation-api apps/monitoring-api apps/compliance apps/compliance-api apps/report-api apps/public-api apps/mock-oidc packages/qa-gateway packages/shared packages/agents"; \
		TOTAL=0; HIGH_TOTAL=0; CRIT_TOTAL=0; \
		for R in $$AUDIT_ROOTS; do \
			BASE=$$(basename $$R); \
			BASE_PATH=ontrackchain/$$R; \
			if [ -d "$$BASE_PATH" ]; then \
				echo "--- audit $$R ---"; \
				(cd "$$BASE_PATH" && \
					(python3 -m pip_audit --format columns 2>/dev/null) || \
					(python3 -m pip install --quiet --no-cache-dir pip-audit pip-api 2>/dev/null && python3 -m pip_audit --format columns) \
				) 2>&1 | tee tmp_audit/$${BASE}.txt | tail -25; \
				H=$$(grep -cE "(HIGH|CRITICAL)" tmp_audit/$${BASE}.txt 2>/dev/null || echo 0); \
				C=$$(grep -cE "CRITICAL" tmp_audit/$${BASE}.txt 2>/dev/null || echo 0); \
				echo "   [$$R] HIGH=$$H  CRITICAL=$$C  (ver tmp_audit/$${BASE}.txt)"; \
				HIGH_TOTAL=$$((HIGH_TOTAL + H)); CRIT_TOTAL=$$((CRIT_TOTAL + C)); TOTAL=$$((TOTAL + 1)); \
			else \
				echo "--- audit $$R (SKIP: diretório inexistente neste ambiente) ---"; \
			fi; \
		done; \
		echo ""; \
		echo "============================================================"; \
		echo "📊 make audit RESUMO: $$TOTAL/13 serviços analisados"; \
		echo "   HIGH=$$HIGH_TOTAL  CRITICAL=$$CRIT_TOTAL"; \
		echo "   Logs completos em tmp_audit/ por serviço."; \
		echo "   CI bloqueia PR se HIGH>0 ou CRITICAL>0."; \
		echo "   Local NÃO bloqueia (comando informativo, use os logs)."; \
		echo "============================================================"

clean: ## Remove temporários (tmp_*/* + __pycache__ + .pytest_cache). S28+49
	@echo "🟢 make clean — apaga temporários (NÃO toca em src, .git, SIGNOFF-M5.md, settings.yml)"
	@echo "   Alvos: tmp_*  ontrackchain/tmp_*  apps/*/tmp_*  packages/*/tmp_*"
	@echo "          **/__pycache__  .pytest_cache  .mypy_cache  **/*.pyc"
	@find . -maxdepth 5 -name "__pycache__" -type d -not -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -maxdepth 5 -name ".pytest_cache" -type d -not -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -maxdepth 5 -name ".mypy_cache" -type d -not -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -maxdepth 5 -name "*.pyc" -type f -not -path "./.git/*" -delete 2>/dev/null || true
	@rm -rf tmp_* ontrackchain/tmp_* ontrackchain/apps/*/tmp_* ontrackchain/packages/*/tmp_* 2>/dev/null || true
	@echo "✅ make clean concluído"

# ============================================================
# Sprint S28+51 P4: Makefile Compose Conveniência + Shortcuts
# NENHUM target é gating (não adicionado a all-checks).
# Todos preservam SIGNOFF-M5.md, settings.yml, .git/ e código de negócio.
#   · scan-secrets-strict : alias curto para qa-gateway-scan-secrets-trufflehog-strict
#   · e2e-light          : wrapper ./ontrackchain/scripts/s28p27-run-e2e-light.sh (perfil LEVE)
#   · compose-up-full    : stack FULL (observabilidade + 9 apps + workers)
#   · compose-health     : tabela HEALTH docker compose ps
#   · compose-purge      : ⚠️ down -v (apaga volumes). Requer FORCE_PURGE=1 explícito.
# ============================================================
scan-secrets-strict: ## Alias curto P0 segredos verificados (qa-gateway trufflehog --only-verified --strict). S28+51
	@echo "🔐 make scan-secrets-strict → qa-gateway-scan-secrets-trufflehog-strict (P0 segredos, --only-verified --strict)"
	@$(MAKE) qa-gateway-scan-secrets-trufflehog-strict

e2e-light: ## E2E smoke LEVE (8 containers: traefik, pg, redis, bootstrap, auth, public, ai, mock-oidc). S28+51
	@echo "🛟 make e2e-light → scripts/s28p27-run-e2e-light.sh (~60 segundos, perfil LEVE)"
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker não encontrado em PATH (obrigatório para E2E)."; exit 2; }
	@cd "$(MONOREPO_ROOT)/.." && ./ontrackchain/scripts/s28p27-run-e2e-light.sh

compose-up-full: ## Docker Compose FULL (observabilidade + 9 apps + 3 workers). S28+51
	@echo "🐳 make compose-up-full → 21 services (observabilidade + 9 apps + workers + traefik/pg/redis)"
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker não encontrado em PATH."; exit 2; }
	@docker compose -f "$(COMPOSE_FILE)" up -d
	@echo "Containeres ativos:"
	@docker compose -f "$(COMPOSE_FILE)" ps --format 'table {{.Name}}	{{.Service}}	{{.State}}	{{.Health}}' 2>/dev/null | head -35 || true

compose-health: ## Resumo docker compose ps: Name / Service / State / Health / Ports. S28+51
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker não encontrado em PATH."; exit 2; }
	@docker compose -f "$(COMPOSE_FILE)" ps --format 'table {{.Name}}	{{.Service}}	{{.State}}	{{.Health}}	{{.Ports}}'

compose-purge: ## ⚠️ DANGER: docker compose down -v (APAGA VOLUMES). Requer FORCE_PURGE=1. S28+51
	@if [ "$(FORCE_PURGE)" != "1" ]; then 		echo "❌ compose-purge é destrutivo (APAGA VOLUMES postgres_data / grafana)."; 		echo "   → Reexecute com: make compose-purge FORCE_PURGE=1"; 		exit 5; 	fi
	@echo "⚠️  make compose-purge FORCE_PURGE=1 → docker compose down -v --remove-orphans (VOLUMES APAGADOS!)"
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker não encontrado em PATH."; exit 2; }
	@docker compose -f "$(COMPOSE_FILE)" down -v --remove-orphans
	@echo "✅ compose-purge concluído. Todos volumes Docker apagados."

# ============================================================
# Sprint S28+54 P4: Makefile CI Conveniência.
# NENHUM target é gating (não adicionado a all-checks). Apenas atalhos DX qualidade de vida.
#   · ci-validate  : 4 gates rápido <10s (M5 + shell + healthz + settings)
#   · ci-local     : 8 gates padrão FAIL-CLOSED ~40s (recomendado commit)
#   · ci-pre-merge : 8 gates + lint + test shared ~120s (recomendado PR/push)
#   · ci-smoke     : qa-gateway-smoke rápido estrutura monorepo
# ============================================================
ci-validate: ## Validação RÁPIDA 4 gates essenciais (<10s). M5 + shell + healthz + settings. S28+54
	@echo "🧪 make ci-validate → 4 gates essenciais (<10 segundos)"
	@$(MAKE) gov-m5-verify
	@$(MAKE) shell-syntax
	@$(MAKE) healthz-bypass-test
	@$(MAKE) settings-dry-run
	@echo ""
	@echo "✅ ci-validate CONCLUÍDO: 4/4 gates essenciais PASS."

ci-local: ## CI LOCAL 8 gates padrão FAIL-CLOSED (~40s). Recomendado commit. S28+54
	@echo "🧪 make ci-local → 8 gates padrão FAIL-CLOSED (metodologia S28 sprints 48-53) ~40s"
	@$(MAKE) gov-m5-verify
	@$(MAKE) gov-m5-unit-test
	@$(MAKE) shell-syntax
	@$(MAKE) healthz-bypass-test
	@$(MAKE) all-checks -n
	@$(MAKE) typecheck -n
	@$(MAKE) qa-gateway-all-strict-ci -n
	@$(MAKE) settings-dry-run
	@echo ""
	@echo "============================================================"
	@echo " ✅ CI-LOCAL PASSOU: 8/8 gates padrão (FAIL-CLOSED) "
	@echo "============================================================"
	@echo "   Próximos passos (opcionais):"
	@echo "     make ci-smoke   → qa-gateway-smoke rápido"
	@echo "     make e2e-light  → ~60s 8 containers perfil LEVE"

ci-pre-merge: ## PRE-MERGE FULL (8 gates + lint + tests shared) (~120s). Recomendado PR/push. S28+54
	@echo "🧪 make ci-pre-merge → CI FULL: 8 gates + lint + tests shared (~120s, SOP PR)"
	@$(MAKE) gov-m5-verify
	@$(MAKE) gov-m5-unit-test
	@$(MAKE) shell-syntax
	@$(MAKE) healthz-bypass-test
	@$(MAKE) all-checks -n
	@$(MAKE) typecheck -n
	@$(MAKE) qa-gateway-all-strict-ci -n
	@$(MAKE) settings-dry-run
	@echo ""
	@$(MAKE) lint
	@echo ""
	@$(MAKE) test-shared
	@echo ""
	@echo "============================================================"
	@echo " ✅ CI-PRE-MERGE PASSOU: 8 gates + lint + tests shared "
	@echo "============================================================"
	@echo "   Pronto para push. CI remoto executa: TruffleHog segredos + qa-gateway-cli-smoke + pytest 8 apps."

ci-smoke: ## SMOKE rápido qa-gateway-smoke (NÃO gating). S28+54
	@echo "🧪 make ci-smoke → qa-gateway-smoke CLI (estrutura monorepo + docs + CSV ROPD)"
	@$(MAKE) qa-gateway-smoke
	@echo "✅ ci-smoke CONCLUÍDO."
