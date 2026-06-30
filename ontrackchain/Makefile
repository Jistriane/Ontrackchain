.PHONY: help help-serious-window prepare-serious-window-dispatch preflight-serious-window-dispatch render-serious-window-dispatch-packet postprocess-serious-window postprocess-serious-window-dry-run

PYTHON ?= python
WINDOW_ID ?= stg-2026-07-06-a
MODE ?= baseline
ENVIRONMENT_NAME ?= staging-serious
DISPATCH_PACKET_OUTPUT_FILE ?= ci-artifacts/serious-window-dispatch-packet-$(WINDOW_ID).md
PAYLOAD_FILE ?= ci-artifacts/prepare-staging-window-output.json
GOVERNANCE_WEEKLY_DIR ?= docs/governance-weekly
RUN_URL ?= pending
SIGNOFF_OUTPUT_FILE ?=

help:
	@echo "Targets disponiveis:"
	@echo "  make prepare-serious-window-dispatch [WINDOW_ID=stg-2026-07-06-a] [MODE=baseline] [ENVIRONMENT_NAME=staging-serious] [DISPATCH_PACKET_OUTPUT_FILE=...]"
	@echo "  make preflight-serious-window-dispatch [WINDOW_ID=stg-2026-07-06-a] [MODE=baseline] [ENVIRONMENT_NAME=staging-serious] [GOVERNANCE_WEEKLY_DIR=...]"
	@echo "  make render-serious-window-dispatch-packet [WINDOW_ID=stg-2026-07-06-a] [MODE=baseline] [ENVIRONMENT_NAME=staging-serious] [DISPATCH_PACKET_OUTPUT_FILE=...]"
	@echo "  make postprocess-serious-window RUN_URL=<github-actions-run-url> [PAYLOAD_FILE=...] [GOVERNANCE_WEEKLY_DIR=...] [SIGNOFF_OUTPUT_FILE=...]"
	@echo "  make help-serious-window"
	@echo "  make postprocess-serious-window-dry-run RUN_URL=<github-actions-run-url> [PAYLOAD_FILE=...] [GOVERNANCE_WEEKLY_DIR=...] [SIGNOFF_OUTPUT_FILE=...]"

help-serious-window:
	@echo "Rito da janela seria:"
	@echo "  1. Executar: make prepare-serious-window-dispatch WINDOW_ID=$(WINDOW_ID)"
	@echo "     ou, se preferir separar, usar os alvos preflight-serious-window-dispatch e render-serious-window-dispatch-packet"
	@echo "  2. Disparar o workflow Staging Serious Window no GitHub Actions"
	@echo "  3. Baixar o artifact serious-staging-window-<janela>"
	@echo "  4. Executar: make postprocess-serious-window RUN_URL=<github-actions-run-url>"
	@echo "  5. Revisar sign-off versionado e board semanal sincronizado"

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
