.PHONY: help help-serious-window prepare-serious-window-dispatch preflight-serious-window-dispatch render-serious-window-dispatch-packet postprocess-serious-window postprocess-serious-window-dry-run run-serious-window-local run-serious-window-local-dry-run check-sanctions-sync-status check-eu-sanctions-window rerun-compliance-worker run-eu-sanctions-window run-eu-sanctions-window-local check-compliance-provider-runtime run-regulatory-readiness-bundle

PYTHON ?= python
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
	@echo "Targets disponiveis:"
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
	@echo "Rito da janela seria:"
	@echo "  1. Executar: make prepare-serious-window-dispatch WINDOW_ID=$(WINDOW_ID)"
	@echo "     ou, se preferir separar, usar os alvos preflight-serious-window-dispatch e render-serious-window-dispatch-packet"
	@echo "  2. Disparar o workflow Staging Serious Window no GitHub Actions"
	@echo "  3. Baixar o artifact serious-staging-window-<janela>"
	@echo "  4. Executar: make postprocess-serious-window RUN_URL=<github-actions-run-url>"
	@echo "  5. Executar: make check-sanctions-sync-status"
	@echo "  6. Executar: make check-eu-sanctions-window quando a janela incluir feed UE tokenizado"
	@echo "  7. No stack dockerizado, executar: make rerun-compliance-worker"
	@echo "  8. Preferencialmente, executar: make run-eu-sanctions-window-local WINDOW_ID=$(WINDOW_ID)"
	@echo "  9. Executar: make check-compliance-provider-runtime INTERNAL_BASE_URL=<url-interna> PUBLIC_BASE_URL=<url-publica>"
	@echo " 10. Alternativamente para P0-02/P0-03 juntos: make run-regulatory-readiness-bundle WINDOW_ID=$(WINDOW_ID)"
	@echo " 11. Para execucao local ponta a ponta: make run-serious-window-local WINDOW_ID=$(WINDOW_ID)"
	@echo " 12. Revisar sign-off versionado e board semanal sincronizado"

prepare-serious-window-dispatch:
	@$(MAKE) preflight-serious-window-dispatch \
		WINDOW_ID="$(WINDOW_ID)" \
		MODE="$(MODE)" \
		ENVIRONMENT_NAME="$(ENVIRONMENT_NAME)" \
		GOVERNANCE_WEEKLY_DIR="$(GOVERNANCE_WEEKLY_DIR)"
	@$(MAKE) render-serious-window-dispatch-packet \
		WINDOW_ID="$(WINDOW_ID)" \
		MODE="$(MODE)" \
		ENVIRONMENT_NAME="$(ENVIRONMENT_NAME)" \
		GOVERNANCE_WEEKLY_DIR="$(GOVERNANCE_WEEKLY_DIR)" \
		DISPATCH_PACKET_OUTPUT_FILE="$(DISPATCH_PACKET_OUTPUT_FILE)"

preflight-serious-window-dispatch:
	@$(PYTHON) scripts/check_serious_window_dispatch_readiness.py \
		--window-id "$(WINDOW_ID)" \
		--mode "$(MODE)" \
		--environment-name "$(ENVIRONMENT_NAME)" \
		--governance-weekly-dir "$(GOVERNANCE_WEEKLY_DIR)"

render-serious-window-dispatch-packet:
	@$(PYTHON) scripts/render_serious_window_dispatch_packet.py \
		--window-id "$(WINDOW_ID)" \
		--mode "$(MODE)" \
		--environment-name "$(ENVIRONMENT_NAME)" \
		--governance-weekly-dir "$(GOVERNANCE_WEEKLY_DIR)" \
		--output-file "$(DISPATCH_PACKET_OUTPUT_FILE)"

postprocess-serious-window:
	@extra_signoff=""; \
	if [ -n "$(SIGNOFF_OUTPUT_FILE)" ]; then \
		extra_signoff=" --signoff-output-file \"$(SIGNOFF_OUTPUT_FILE)\""; \
	fi; \
	$(PYTHON) scripts/postprocess_staging_window_artifact.py \
		--payload-file "$(PAYLOAD_FILE)" \
		--governance-weekly-dir "$(GOVERNANCE_WEEKLY_DIR)" \
		--run-url "$(RUN_URL)"$$extra_signoff

postprocess-serious-window-dry-run:
	@extra_signoff=""; \
	if [ -n "$(SIGNOFF_OUTPUT_FILE)" ]; then \
		extra_signoff=" --signoff-output-file \"$(SIGNOFF_OUTPUT_FILE)\""; \
	fi; \
	printf '%s\n' "$(PYTHON) scripts/postprocess_staging_window_artifact.py --payload-file \"$(PAYLOAD_FILE)\" --governance-weekly-dir \"$(GOVERNANCE_WEEKLY_DIR)\" --run-url \"$(RUN_URL)\"$$extra_signoff"

run-serious-window-local:
	@mkdir -p "$(dir $(PAYLOAD_FILE))"
	@$(PYTHON) scripts/prepare_staging_window.py \
		--window-id "$(WINDOW_ID)" \
		--mode "$(MODE)" \
		--private-env-file "$(PRIVATE_ENV_FILE)" \
		--checks-dir "artifacts/staging/checks" \
		--dossiers-dir "artifacts/staging/dossiers" \
		--homologation-dir "artifacts/homologation" \
		--window-packet-dir "artifacts/staging" \
		--run > "$(PAYLOAD_FILE)"
	@$(PYTHON) scripts/postprocess_staging_window_artifact.py \
		--payload-file "$(PAYLOAD_FILE)" \
		--governance-weekly-dir "$(GOVERNANCE_WEEKLY_DIR)" \
		--run-url "$(LOCAL_RUN_URL)"

run-serious-window-local-dry-run:
	@printf '%s\n' "$(PYTHON) scripts/prepare_staging_window.py --window-id \"$(WINDOW_ID)\" --mode \"$(MODE)\" --private-env-file \"$(PRIVATE_ENV_FILE)\" --checks-dir \"artifacts/staging/checks\" --dossiers-dir \"artifacts/staging/dossiers\" --homologation-dir \"artifacts/homologation\" --window-packet-dir \"artifacts/staging\" --run > \"$(PAYLOAD_FILE)\""
	@printf '%s\n' "$(PYTHON) scripts/postprocess_staging_window_artifact.py --payload-file \"$(PAYLOAD_FILE)\" --governance-weekly-dir \"$(GOVERNANCE_WEEKLY_DIR)\" --run-url \"$(LOCAL_RUN_URL)\""

check-sanctions-sync-status:
	@$(PYTHON) scripts/check_sanctions_sync_status.py

check-eu-sanctions-window:
	@$(PYTHON) scripts/check_sanctions_sync_status.py --eu-window

rerun-compliance-worker:
	@docker compose up -d compliance-worker

run-eu-sanctions-window:
	@private_env_args=""; \
	checks_dir_args=""; \
	if [ -n "$(PRIVATE_ENV_FILE)" ]; then \
		private_env_args=" --private-env-file \"$(PRIVATE_ENV_FILE)\""; \
	fi; \
	if [ -n "$(CHECKS_DIR)" ]; then \
		checks_dir_args=" --checks-dir \"$(CHECKS_DIR)\""; \
	fi; \
	eval $(PYTHON) scripts/run_eu_sanctions_window.py --window-id "\"$(WINDOW_ID)\""$$private_env_args$$checks_dir_args

run-eu-sanctions-window-local:
	@$(MAKE) rerun-compliance-worker
	@$(MAKE) run-eu-sanctions-window \
		WINDOW_ID="$(WINDOW_ID)" \
		PRIVATE_ENV_FILE="$(PRIVATE_ENV_FILE)" \
		CHECKS_DIR="$(CHECKS_DIR)"

check-compliance-provider-runtime:
	@internal_base_args=""; \
	public_base_args=""; \
	if [ -n "$(INTERNAL_BASE_URL)" ]; then \
		internal_base_args=" --internal-base-url \"$(INTERNAL_BASE_URL)\""; \
	fi; \
	if [ -n "$(PUBLIC_BASE_URL)" ]; then \
		public_base_args=" --public-base-url \"$(PUBLIC_BASE_URL)\""; \
	fi; \
	eval $(PYTHON) scripts/check_compliance_provider_runtime.py$$internal_base_args$$public_base_args

run-regulatory-readiness-bundle:
	@internal_base_args=""; \
	public_base_args=""; \
	private_env_args=""; \
	checks_dir_args=""; \
	if [ -n "$(INTERNAL_BASE_URL)" ]; then \
		internal_base_args=" --internal-base-url \"$(INTERNAL_BASE_URL)\""; \
	fi; \
	if [ -n "$(PUBLIC_BASE_URL)" ]; then \
		public_base_args=" --public-base-url \"$(PUBLIC_BASE_URL)\""; \
	fi; \
	if [ -n "$(PRIVATE_ENV_FILE)" ]; then \
		private_env_args=" --private-env-file \"$(PRIVATE_ENV_FILE)\""; \
	fi; \
	if [ -n "$(CHECKS_DIR)" ]; then \
		checks_dir_args=" --checks-dir \"$(CHECKS_DIR)\""; \
	fi; \
	eval $(PYTHON) scripts/run_regulatory_readiness_bundle.py --window-id "\"$(WINDOW_ID)\""$$private_env_args$$checks_dir_args$$internal_base_args$$public_base_args
