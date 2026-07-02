.PHONY: help help-serious-window prepare-serious-window-dispatch preflight-serious-window-dispatch render-serious-window-dispatch-packet postprocess-serious-window postprocess-serious-window-dry-run run-serious-window-local run-serious-window-local-dry-run check-sanctions-sync-status check-eu-sanctions-window rerun-compliance-worker run-eu-sanctions-window run-eu-sanctions-window-local check-compliance-provider-runtime run-regulatory-readiness-bundle

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
