.PHONY: help help-serious-window start-oidc-local stop-oidc-local gate-p0-01-oidc-local gate-p0-01-oidc-ci gate-p0-02-aml-live gate-p0-03-eu-live gate-p0-04-regulatory-bundle gate-p0-05-serious-window prepare-serious-window-dispatch preflight-serious-window-dispatch render-serious-window-dispatch-packet postprocess-serious-window postprocess-serious-window-dry-run run-serious-window-local run-serious-window-local-dry-run check-sanctions-sync-status check-eu-sanctions-window rerun-compliance-worker run-eu-sanctions-window run-eu-sanctions-window-local check-compliance-provider-runtime run-regulatory-readiness-bundle run-regulatory-readiness-bundle-local render-regulatory-readiness-bundle run-oidc-readiness-bundle run-oidc-readiness-bundle-local render-oidc-readiness-bundle validate-serious-window-artifact validate-serious-window-artifact-local render-staging-war-room-action-plan build-operational-alerts-rca-summary run-staging-window-status-snapshot-local render-staging-window-status-snapshot render-staging-window-status-snapshot-delta render-staging-governance-dashboard render-staging-unblock-checklist render-staging-comms-summary render-staging-executive-bullet render-staging-governance-consolidated-json notify-slack-governance evaluate-governance-gate track-governance-history render-governance-gate-history-dashboard update-governance-metrics refresh-staging-war-room-governance-local apply-regulatory-work-items-migration apply-regulatory-work-items-contract-guardrails-migration check-work-items-contracts validate-work-items-runtime-local smoke-work-items-ownership-backend alert-pagerduty-governance-blocks generate-environment-promotion-policy generate-compliance-report generate-compliance-reports-all evaluate-auto-promotion-readiness check-workflow-hygiene prune-governance-weekly-archive prune-governance-weekly-archive-dry-run

PYTHON ?= python3
GOVERNANCE_WEEKLY_ARCHIVE_RETENTION_DAYS ?= 90
WINDOW_ID ?= stg-2026-07-06-a
MODE ?= baseline
ENVIRONMENT_NAME ?= staging-serious
DISPATCH_PACKET_OUTPUT_FILE ?= ci-artifacts/serious-window-dispatch-packet-$(WINDOW_ID).md
PAYLOAD_FILE ?= ci-artifacts/prepare-staging-window-output.json
GOVERNANCE_WEEKLY_DIR ?= docs/governance-weekly
WINDOW_ARTIFACTS_DIR ?= $(GOVERNANCE_WEEKLY_DIR)/generated/windows/$(WINDOW_ID)
GATE_ARTIFACTS_DIR ?= $(GOVERNANCE_WEEKLY_DIR)/generated/gates
RUN_URL ?= pending
SIGNOFF_OUTPUT_FILE ?=
PRIVATE_ENV_FILE ?= .env.staging.private
LOCAL_RUN_URL ?= local://staging-serious/$(WINDOW_ID)
BUNDLE_OUTPUT_FILE ?= artifacts/staging/checks/$(WINDOW_ID)-regulatory-readiness-bundle.json
BUNDLE_SUMMARY_FILE ?= artifacts/staging/dossiers/$(WINDOW_ID)-regulatory-readiness-bundle.md
OIDC_BUNDLE_OUTPUT_FILE ?= artifacts/staging/checks/$(WINDOW_ID)-oidc-readiness-bundle.json
OIDC_BUNDLE_SUMMARY_FILE ?= artifacts/staging/dossiers/$(WINDOW_ID)-oidc-readiness-bundle.md
CHECKS_DIR ?= artifacts/staging/checks
DOSSIERS_DIR ?= artifacts/staging/dossiers
ART_SCOPE ?= P0-01,P0-02,P0-03
OPERATIONAL_ALERTS_EXPORT_INPUT_FILE ?= $(CHECKS_DIR)/$(WINDOW_ID)-operational-alerts-export.json
OPERATIONAL_ALERTS_RCA_SUMMARY_OUTPUT_FILE ?= $(CHECKS_DIR)/$(WINDOW_ID)-operational-alerts-rca-summary.json
WAR_ROOM_ACTION_PLAN_OUTPUT_FILE ?= $(WINDOW_ARTIFACTS_DIR)/$(WINDOW_ID)-war-room-action-plan.md
STATUS_SNAPSHOT_OUTPUT_FILE ?= artifacts/staging/checks/$(WINDOW_ID)-status-snapshot.json
STATUS_SNAPSHOT_MARKDOWN_OUTPUT_FILE ?= $(WINDOW_ARTIFACTS_DIR)/$(WINDOW_ID)-status-snapshot.md
STATUS_SNAPSHOT_HISTORY_DIR ?= artifacts/staging/checks/history
STATUS_SNAPSHOT_DELTA_OUTPUT_FILE ?= $(WINDOW_ARTIFACTS_DIR)/$(WINDOW_ID)-status-snapshot-delta.md
GOVERNANCE_DASHBOARD_OUTPUT_FILE ?= $(WINDOW_ARTIFACTS_DIR)/$(WINDOW_ID)-governance-dashboard.md
UNBLOCK_CHECKLIST_OUTPUT_FILE ?= $(WINDOW_ARTIFACTS_DIR)/$(WINDOW_ID)-unblock-checklist.md
COMMS_SUMMARY_OUTPUT_FILE ?= $(WINDOW_ARTIFACTS_DIR)/$(WINDOW_ID)-comms-summary.md
EXECUTIVE_BULLET_OUTPUT_FILE ?= $(WINDOW_ARTIFACTS_DIR)/$(WINDOW_ID)-executive-bullet.md
CONSOLIDATED_JSON_OUTPUT_FILE ?= $(WINDOW_ARTIFACTS_DIR)/$(WINDOW_ID)-consolidated.json
SLACK_WEBHOOK_URL ?=
GATE_POLICY ?= strict
GATE_OPERATION ?= merge
OIDC_LOCAL_ENV_FILE ?= .env.oidc-local
OIDC_LOCAL_BASE_URL ?= http://localhost:8080
OIDC_CI_BASE_URL ?= http://localhost:8080
COMPLIANCE_INTERNAL_BASE_URL ?= http://localhost:8002
COMPLIANCE_PUBLIC_BASE_URL ?= http://localhost:8080
REQUEST_ID ?=

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
	@echo "  make check-sanctions-sync-status [REQUEST_ID=...]"
	@echo "  make check-eu-sanctions-window [REQUEST_ID=...]"
	@echo "  make rerun-compliance-worker"
	@echo "  make run-eu-sanctions-window [WINDOW_ID=...] [PRIVATE_ENV_FILE=...] [CHECKS_DIR=...]"
	@echo "  make run-eu-sanctions-window-local [WINDOW_ID=...] [PRIVATE_ENV_FILE=...] [CHECKS_DIR=...]"
	@echo "  make check-compliance-provider-runtime [INTERNAL_BASE_URL=...] [PUBLIC_BASE_URL=...]"
	@echo "  make run-regulatory-readiness-bundle [WINDOW_ID=...] [PRIVATE_ENV_FILE=...] [CHECKS_DIR=...] [INTERNAL_BASE_URL=...] [PUBLIC_BASE_URL=...]"
	@echo "  make run-regulatory-readiness-bundle-local [WINDOW_ID=...] [PRIVATE_ENV_FILE=...] [CHECKS_DIR=...] [BUNDLE_OUTPUT_FILE=...] [BUNDLE_SUMMARY_FILE=...]"
	@echo "  make render-regulatory-readiness-bundle [BUNDLE_OUTPUT_FILE=...] [BUNDLE_SUMMARY_FILE=...]"
	@echo "  make check-regulatory-window-readiness [REGULATORY_SCOPE=p0-02|p0-03|p0-04] [PRIVATE_ENV_FILE=.env.staging.private] [OWNERSHIP_FILE=docs/staging-env-ownership.md]"
	@echo "  make run-oidc-readiness-bundle [WINDOW_ID=...] [PRIVATE_ENV_FILE=...] [CHECKS_DIR=...] [BASE_URL=...]"
	@echo "  make run-oidc-readiness-bundle-local [WINDOW_ID=...] [PRIVATE_ENV_FILE=...] [CHECKS_DIR=...] [OIDC_BUNDLE_OUTPUT_FILE=...] [OIDC_BUNDLE_SUMMARY_FILE=...] [BASE_URL=...]"
	@echo "  make render-oidc-readiness-bundle [OIDC_BUNDLE_OUTPUT_FILE=...] [OIDC_BUNDLE_SUMMARY_FILE=...]"
	@echo "  make start-oidc-local [OIDC_LOCAL_ENV_FILE=.env.oidc-local]"
	@echo "  make stop-oidc-local [OIDC_LOCAL_ENV_FILE=.env.oidc-local]"
	@echo "  make gate-p0-01-oidc-local [OIDC_LOCAL_ENV_FILE=.env.oidc-local] [OIDC_LOCAL_BASE_URL=http://localhost:8080]"
	@echo "  make gate-p0-01-oidc-ci [OIDC_CI_BASE_URL=http://localhost:8080]"
	@echo "  make gate-p0-02-aml-live [PRIVATE_ENV_FILE=.env.staging.private] [COMPLIANCE_INTERNAL_BASE_URL=http://localhost:8002] [COMPLIANCE_PUBLIC_BASE_URL=http://localhost:8080]"
	@echo "  make gate-p0-03-eu-live [WINDOW_ID=...] [PRIVATE_ENV_FILE=.env.staging.private] [CHECKS_DIR=artifacts/staging/checks]"
	@echo "  make gate-p0-04-regulatory-bundle [WINDOW_ID=...] [PRIVATE_ENV_FILE=.env.staging.private] [CHECKS_DIR=artifacts/staging/checks] [DOSSIERS_DIR=artifacts/staging/dossiers]"
	@echo "  make gate-p0-05-serious-window [WINDOW_ID=...] [MODE=baseline] [PRIVATE_ENV_FILE=.env.staging.private] [GOVERNANCE_WEEKLY_DIR=docs/governance-weekly]"
	@echo "  make validate-serious-window-artifact [WINDOW_ID=...] [CHECKS_DIR=...] [DOSSIERS_DIR=...] [ART_SCOPE=P0-01,P0-02,P0-03]"
	@echo "  make validate-serious-window-artifact-local [WINDOW_ID=...]"
	@echo "  make render-staging-war-room-action-plan [WINDOW_ID=...] [CHECKS_DIR=...] [WAR_ROOM_ACTION_PLAN_OUTPUT_FILE=...]"
	@echo "  make run-staging-window-status-snapshot-local [WINDOW_ID=...] [PRIVATE_ENV_FILE=...] [CHECKS_DIR=...] [DOSSIERS_DIR=...] [ART_SCOPE=...] [STATUS_SNAPSHOT_OUTPUT_FILE=...]"
	@echo "  make build-operational-alerts-rca-summary [WINDOW_ID=...] [OPERATIONAL_ALERTS_EXPORT_INPUT_FILE=...] [OPERATIONAL_ALERTS_RCA_SUMMARY_OUTPUT_FILE=...]"
	@echo "  make render-staging-window-status-snapshot [STATUS_SNAPSHOT_OUTPUT_FILE=...] [STATUS_SNAPSHOT_MARKDOWN_OUTPUT_FILE=...]"
	@echo "  make render-staging-window-status-snapshot-delta [WINDOW_ID=...] [STATUS_SNAPSHOT_HISTORY_DIR=...] [STATUS_SNAPSHOT_DELTA_OUTPUT_FILE=...]"
	@echo "  make render-staging-governance-dashboard [WINDOW_ID=...] [STATUS_SNAPSHOT_HISTORY_DIR=...] [GOVERNANCE_DASHBOARD_OUTPUT_FILE=...]"
	@echo "  make render-staging-unblock-checklist [WINDOW_ID=...] [STATUS_SNAPSHOT_OUTPUT_FILE=...] [UNBLOCK_CHECKLIST_OUTPUT_FILE=...]"
	@echo "  make render-staging-comms-summary [WINDOW_ID=...] [STATUS_SNAPSHOT_OUTPUT_FILE=...] [STATUS_SNAPSHOT_DELTA_OUTPUT_FILE=...] [GOVERNANCE_DASHBOARD_OUTPUT_FILE=...] [UNBLOCK_CHECKLIST_OUTPUT_FILE=...] [COMMS_SUMMARY_OUTPUT_FILE=...]"
	@echo "  make render-staging-executive-bullet [WINDOW_ID=...] [STATUS_SNAPSHOT_OUTPUT_FILE=...] [STATUS_SNAPSHOT_DELTA_OUTPUT_FILE=...] [EXECUTIVE_BULLET_OUTPUT_FILE=...]"
	@echo "  make refresh-staging-war-room-governance-local [WINDOW_ID=...] [CHECKS_DIR=...] [PRIVATE_ENV_FILE=...] [DOSSIERS_DIR=...]"
	@echo "  make apply-regulatory-work-items-migration"
	@echo "  make apply-regulatory-work-items-contract-guardrails-migration"
	@echo "  make apply-evidence-package-seals-migration"
	@echo "  make apply-team-users-directory-migration"
	@echo "  make check-work-items-contracts"
	@echo "  make validate-work-items-runtime-local"
	@echo "  make smoke-work-items-ownership-backend"
	@echo "  make check-workflow-hygiene"
	@echo "  make prune-governance-weekly-archive [GOVERNANCE_WEEKLY_ARCHIVE_RETENTION_DAYS=90]"
	@echo "  make prune-governance-weekly-archive-dry-run [GOVERNANCE_WEEKLY_ARCHIVE_RETENTION_DAYS=90]"

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
	@echo " 11. Para artefato local da Sprint 7: make run-regulatory-readiness-bundle-local WINDOW_ID=$(WINDOW_ID)"
	@echo " 12. Para P0-01 local: make gate-p0-01-oidc-local OIDC_LOCAL_ENV_FILE=$(OIDC_LOCAL_ENV_FILE) OIDC_LOCAL_BASE_URL=$(OIDC_LOCAL_BASE_URL)"
	@echo "     depois gerar o bundle: make run-oidc-readiness-bundle-local WINDOW_ID=$(WINDOW_ID) BASE_URL=$(OIDC_LOCAL_BASE_URL)"
	@echo " 13. Para P0-02 local: make gate-p0-02-aml-live PRIVATE_ENV_FILE=$(PRIVATE_ENV_FILE) COMPLIANCE_INTERNAL_BASE_URL=$(COMPLIANCE_INTERNAL_BASE_URL) COMPLIANCE_PUBLIC_BASE_URL=$(COMPLIANCE_PUBLIC_BASE_URL)"
	@echo " 14. Para P0-03 local: make gate-p0-03-eu-live WINDOW_ID=$(WINDOW_ID) PRIVATE_ENV_FILE=$(PRIVATE_ENV_FILE) CHECKS_DIR=$(CHECKS_DIR)"
	@echo " 15. Para P0-04 local: make gate-p0-04-regulatory-bundle WINDOW_ID=$(WINDOW_ID) PRIVATE_ENV_FILE=$(PRIVATE_ENV_FILE) CHECKS_DIR=$(CHECKS_DIR) DOSSIERS_DIR=$(DOSSIERS_DIR)"
	@echo " 16. Para P0-05 local: make gate-p0-05-serious-window WINDOW_ID=$(WINDOW_ID) MODE=$(MODE) PRIVATE_ENV_FILE=$(PRIVATE_ENV_FILE)"
	@echo " 17. Para execucao local ponta a ponta: make run-serious-window-local WINDOW_ID=$(WINDOW_ID)"
	@echo " 18. Validar completude do artifact: make validate-serious-window-artifact-local WINDOW_ID=$(WINDOW_ID)"
	@echo " 18.1 Opcional para RCA cross-domain: make build-operational-alerts-rca-summary WINDOW_ID=$(WINDOW_ID) OPERATIONAL_ALERTS_EXPORT_INPUT_FILE=<export-json>"
	@echo " 19. Atualizar pacote local de governanca: make refresh-staging-war-room-governance-local WINDOW_ID=$(WINDOW_ID)"
	@echo " 20. Revisar sign-off versionado e board semanal sincronizado"

start-oidc-local:
	@bash scripts/start_oidc_local.sh "$(OIDC_LOCAL_ENV_FILE)"

stop-oidc-local:
	@bash scripts/stop_oidc_local.sh "$(OIDC_LOCAL_ENV_FILE)"

gate-p0-01-oidc-local:
	@bash scripts/run_p0_01_oidc_local_gate.sh "$(OIDC_LOCAL_ENV_FILE)" "$(OIDC_LOCAL_BASE_URL)"

gate-p0-01-oidc-ci:
	@bash scripts/run_p0_01_oidc_ci_gate.sh "$(OIDC_CI_BASE_URL)"

gate-p0-02-aml-live:
	@ENV_FILE="$(PRIVATE_ENV_FILE)" \
	INTERNAL_BASE_URL="$(COMPLIANCE_INTERNAL_BASE_URL)" \
	PUBLIC_BASE_URL="$(COMPLIANCE_PUBLIC_BASE_URL)" \
	bash scripts/run_p0_02_aml_live_gate.sh

gate-p0-03-eu-live:
	@ENV_FILE="$(PRIVATE_ENV_FILE)" \
	WINDOW_ID="$(WINDOW_ID)" \
	REQUEST_ID="$(REQUEST_ID)" \
	CHECKS_DIR="$(CHECKS_DIR)" \
	bash scripts/run_p0_03_eu_live_gate.sh

gate-p0-04-regulatory-bundle:
	@ENV_FILE="$(PRIVATE_ENV_FILE)" \
	WINDOW_ID="$(WINDOW_ID)" \
	CHECKS_DIR="$(CHECKS_DIR)" \
	DOSSIERS_DIR="$(DOSSIERS_DIR)" \
	INTERNAL_BASE_URL="$(COMPLIANCE_INTERNAL_BASE_URL)" \
	PUBLIC_BASE_URL="$(COMPLIANCE_PUBLIC_BASE_URL)" \
	bash scripts/run_p0_04_regulatory_bundle_gate.sh

gate-p0-05-serious-window:
	@ENV_FILE="$(PRIVATE_ENV_FILE)" \
	WINDOW_ID="$(WINDOW_ID)" \
	MODE="$(MODE)" \
	GOVERNANCE_WEEKLY_DIR="$(GOVERNANCE_WEEKLY_DIR)" \
	RUN_URL="$(LOCAL_RUN_URL)" \
	bash scripts/run_p0_05_serious_window_gate.sh

check-regulatory-window-readiness:
	@$(PYTHON) scripts/check_regulatory_window_readiness.py \
		--scope "$(REGULATORY_SCOPE)" \
		--private-env-file "$(PRIVATE_ENV_FILE)" \
		--ownership-file "$(OWNERSHIP_FILE)"

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
	@request_id_args=""; \
	if [ -n "$(REQUEST_ID)" ]; then \
		request_id_args=" --request-id \"$(REQUEST_ID)\""; \
	fi; \
	eval $(PYTHON) scripts/check_sanctions_sync_status.py$$request_id_args

check-eu-sanctions-window:
	@request_id_args=""; \
	if [ -n "$(REQUEST_ID)" ]; then \
		request_id_args=" --request-id \"$(REQUEST_ID)\""; \
	fi; \
	eval $(PYTHON) scripts/check_sanctions_sync_status.py --eu-window$$request_id_args

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

run-regulatory-readiness-bundle-local:
	@mkdir -p "$(dir $(BUNDLE_OUTPUT_FILE))" "$(dir $(BUNDLE_SUMMARY_FILE))"
	@set +e; \
	internal_base_args=""; \
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
	eval $(PYTHON) scripts/run_regulatory_readiness_bundle.py --window-id "\"$(WINDOW_ID)\""$$private_env_args$$checks_dir_args$$internal_base_args$$public_base_args > "$(BUNDLE_OUTPUT_FILE)" 2>&1; \
	exit_code=$$?; \
	$(MAKE) --no-print-directory render-regulatory-readiness-bundle \
		BUNDLE_OUTPUT_FILE="$(BUNDLE_OUTPUT_FILE)" \
		BUNDLE_SUMMARY_FILE="$(BUNDLE_SUMMARY_FILE)"; \
	exit $$exit_code

render-regulatory-readiness-bundle:
	@$(PYTHON) scripts/render_regulatory_readiness_bundle.py \
		--bundle-file "$(BUNDLE_OUTPUT_FILE)" \
		--output-file "$(BUNDLE_SUMMARY_FILE)"

run-oidc-readiness-bundle:
	@private_env_args=""; \
	checks_dir_args=""; \
	base_url_args=""; \
	if [ -n "$(PRIVATE_ENV_FILE)" ]; then \
		private_env_args=" --private-env-file \"$(PRIVATE_ENV_FILE)\""; \
	fi; \
	if [ -n "$(CHECKS_DIR)" ]; then \
		checks_dir_args=" --checks-dir \"$(CHECKS_DIR)\""; \
	fi; \
	if [ -n "$(BASE_URL)" ]; then \
		base_url_args=" --base-url \"$(BASE_URL)\""; \
	fi; \
	eval $(PYTHON) scripts/run_oidc_readiness_bundle.py --window-id "\"$(WINDOW_ID)\""$$private_env_args$$checks_dir_args$$base_url_args

run-oidc-readiness-bundle-local:
	@mkdir -p "$(dir $(OIDC_BUNDLE_OUTPUT_FILE))" "$(dir $(OIDC_BUNDLE_SUMMARY_FILE))"
	@set +e; \
	private_env_args=""; \
	checks_dir_args=""; \
	base_url_args=""; \
	if [ -n "$(PRIVATE_ENV_FILE)" ]; then \
		private_env_args=" --private-env-file \"$(PRIVATE_ENV_FILE)\""; \
	fi; \
	if [ -n "$(CHECKS_DIR)" ]; then \
		checks_dir_args=" --checks-dir \"$(CHECKS_DIR)\""; \
	fi; \
	if [ -n "$(BASE_URL)" ]; then \
		base_url_args=" --base-url \"$(BASE_URL)\""; \
	fi; \
	eval $(PYTHON) scripts/run_oidc_readiness_bundle.py --window-id "\"$(WINDOW_ID)\""$$private_env_args$$checks_dir_args$$base_url_args > "$(OIDC_BUNDLE_OUTPUT_FILE)" 2>&1; \
	exit_code=$$?; \
	$(MAKE) --no-print-directory render-oidc-readiness-bundle \
		OIDC_BUNDLE_OUTPUT_FILE="$(OIDC_BUNDLE_OUTPUT_FILE)" \
		OIDC_BUNDLE_SUMMARY_FILE="$(OIDC_BUNDLE_SUMMARY_FILE)"; \
	exit $$exit_code

render-oidc-readiness-bundle:
	@$(PYTHON) scripts/render_oidc_readiness_bundle.py \
		--bundle-file "$(OIDC_BUNDLE_OUTPUT_FILE)" \
		--output-file "$(OIDC_BUNDLE_SUMMARY_FILE)"

validate-serious-window-artifact:
	@$(PYTHON) scripts/validate_serious_window_artifact.py \
		--window-id "$(WINDOW_ID)" \
		--checks-dir "$(CHECKS_DIR)" \
		--dossiers-dir "$(DOSSIERS_DIR)" \
		--scope "$(ART_SCOPE)"

validate-serious-window-artifact-local:
	@$(MAKE) --no-print-directory validate-serious-window-artifact \
		WINDOW_ID="$(WINDOW_ID)" \
		CHECKS_DIR="artifacts/staging/checks" \
		DOSSIERS_DIR="artifacts/staging/dossiers" \
		ART_SCOPE="P0-01,P0-02,P0-03"

render-staging-war-room-action-plan:
	@mkdir -p "$(dir $(WAR_ROOM_ACTION_PLAN_OUTPUT_FILE))"
	@$(PYTHON) scripts/render_staging_war_room_action_plan.py \
		--window-id "$(WINDOW_ID)" \
		--checks-dir "$(CHECKS_DIR)" \
		--output-file "$(WAR_ROOM_ACTION_PLAN_OUTPUT_FILE)"

build-operational-alerts-rca-summary:
	@mkdir -p "$(dir $(OPERATIONAL_ALERTS_RCA_SUMMARY_OUTPUT_FILE))"
	@$(PYTHON) scripts/build_operational_alerts_rca_summary.py \
		--window-id "$(WINDOW_ID)" \
		--input-file "$(OPERATIONAL_ALERTS_EXPORT_INPUT_FILE)" \
		--output-file "$(OPERATIONAL_ALERTS_RCA_SUMMARY_OUTPUT_FILE)"

run-staging-window-status-snapshot-local:
	@$(PYTHON) scripts/run_staging_window_status_snapshot.py \
		--window-id "$(WINDOW_ID)" \
		--private-env-file "$(PRIVATE_ENV_FILE)" \
		--checks-dir "$(CHECKS_DIR)" \
		--dossiers-dir "$(DOSSIERS_DIR)" \
		--scope "$(ART_SCOPE)" \
		--output-file "$(STATUS_SNAPSHOT_OUTPUT_FILE)" \
		--history-dir "$(STATUS_SNAPSHOT_HISTORY_DIR)"
	@$(MAKE) --no-print-directory render-staging-window-status-snapshot \
		STATUS_SNAPSHOT_OUTPUT_FILE="$(STATUS_SNAPSHOT_OUTPUT_FILE)" \
		STATUS_SNAPSHOT_MARKDOWN_OUTPUT_FILE="$(STATUS_SNAPSHOT_MARKDOWN_OUTPUT_FILE)"
	@$(MAKE) --no-print-directory render-staging-window-status-snapshot-delta \
		WINDOW_ID="$(WINDOW_ID)" \
		STATUS_SNAPSHOT_HISTORY_DIR="$(STATUS_SNAPSHOT_HISTORY_DIR)" \
		STATUS_SNAPSHOT_DELTA_OUTPUT_FILE="$(STATUS_SNAPSHOT_DELTA_OUTPUT_FILE)"

render-staging-window-status-snapshot:
	@mkdir -p "$(dir $(STATUS_SNAPSHOT_MARKDOWN_OUTPUT_FILE))"
	@$(PYTHON) scripts/render_staging_window_status_snapshot.py \
		--snapshot-file "$(STATUS_SNAPSHOT_OUTPUT_FILE)" \
		--output-file "$(STATUS_SNAPSHOT_MARKDOWN_OUTPUT_FILE)"

render-staging-window-status-snapshot-delta:
	@mkdir -p "$(dir $(STATUS_SNAPSHOT_DELTA_OUTPUT_FILE))"
	@$(PYTHON) scripts/render_staging_window_status_snapshot_delta.py \
		--window-id "$(WINDOW_ID)" \
		--history-dir "$(STATUS_SNAPSHOT_HISTORY_DIR)" \
		--output-file "$(STATUS_SNAPSHOT_DELTA_OUTPUT_FILE)"

render-staging-governance-dashboard:
	@mkdir -p "$(dir $(GOVERNANCE_DASHBOARD_OUTPUT_FILE))"
	@$(PYTHON) scripts/render_staging_governance_dashboard.py \
		--window-id "$(WINDOW_ID)" \
		--history-dir "$(STATUS_SNAPSHOT_HISTORY_DIR)" \
		--action-plan-file "$(WAR_ROOM_ACTION_PLAN_OUTPUT_FILE)" \
		--status-snapshot-file "$(STATUS_SNAPSHOT_MARKDOWN_OUTPUT_FILE)" \
		--status-delta-file "$(STATUS_SNAPSHOT_DELTA_OUTPUT_FILE)" \
		--output-file "$(GOVERNANCE_DASHBOARD_OUTPUT_FILE)"

render-staging-unblock-checklist:
	@mkdir -p "$(dir $(UNBLOCK_CHECKLIST_OUTPUT_FILE))"
	@$(PYTHON) scripts/render_staging_unblock_checklist.py \
		--window-id "$(WINDOW_ID)" \
		--snapshot-file "$(STATUS_SNAPSHOT_OUTPUT_FILE)" \
		--output-file "$(UNBLOCK_CHECKLIST_OUTPUT_FILE)"

render-staging-comms-summary:
	@mkdir -p "$(dir $(COMMS_SUMMARY_OUTPUT_FILE))"
	@$(PYTHON) scripts/render_staging_comms_summary.py \
		--window-id "$(WINDOW_ID)" \
		--snapshot-file "$(STATUS_SNAPSHOT_OUTPUT_FILE)" \
		--delta-file "$(STATUS_SNAPSHOT_DELTA_OUTPUT_FILE)" \
		--dashboard-file "$(GOVERNANCE_DASHBOARD_OUTPUT_FILE)" \
		--unblock-file "$(UNBLOCK_CHECKLIST_OUTPUT_FILE)" \
		--output-file "$(COMMS_SUMMARY_OUTPUT_FILE)"

render-staging-executive-bullet:
	@mkdir -p "$(dir $(EXECUTIVE_BULLET_OUTPUT_FILE))"
	@$(PYTHON) scripts/render_staging_executive_bullet.py \
		--window-id "$(WINDOW_ID)" \
		--snapshot-file "$(STATUS_SNAPSHOT_OUTPUT_FILE)" \
		--delta-file "$(STATUS_SNAPSHOT_DELTA_OUTPUT_FILE)" \
		--output-file "$(EXECUTIVE_BULLET_OUTPUT_FILE)"

render-staging-governance-consolidated-json:
	@mkdir -p "$(dir $(CONSOLIDATED_JSON_OUTPUT_FILE))"
	@$(PYTHON) scripts/render_staging_governance_consolidated_json.py \
		--window-id "$(WINDOW_ID)" \
		--checks-dir "$(CHECKS_DIR)" \
		--dossiers-dir "$(DOSSIERS_DIR)" \
		--docs-dir "$(WINDOW_ARTIFACTS_DIR)" \
		--output-file "$(CONSOLIDATED_JSON_OUTPUT_FILE)"

refresh-staging-war-room-governance-local:
	@mkdir -p "$(WINDOW_ARTIFACTS_DIR)" "$(GATE_ARTIFACTS_DIR)"
	@$(MAKE) --no-print-directory render-staging-war-room-action-plan \
		WINDOW_ID="$(WINDOW_ID)" \
		CHECKS_DIR="$(CHECKS_DIR)" \
		WAR_ROOM_ACTION_PLAN_OUTPUT_FILE="$(WAR_ROOM_ACTION_PLAN_OUTPUT_FILE)"
	@$(MAKE) --no-print-directory run-staging-window-status-snapshot-local \
		WINDOW_ID="$(WINDOW_ID)" \
		PRIVATE_ENV_FILE="$(PRIVATE_ENV_FILE)" \
		CHECKS_DIR="$(CHECKS_DIR)" \
		DOSSIERS_DIR="$(DOSSIERS_DIR)" \
		ART_SCOPE="$(ART_SCOPE)" \
		STATUS_SNAPSHOT_OUTPUT_FILE="$(STATUS_SNAPSHOT_OUTPUT_FILE)" \
		STATUS_SNAPSHOT_MARKDOWN_OUTPUT_FILE="$(STATUS_SNAPSHOT_MARKDOWN_OUTPUT_FILE)" \
		STATUS_SNAPSHOT_HISTORY_DIR="$(STATUS_SNAPSHOT_HISTORY_DIR)" \
		STATUS_SNAPSHOT_DELTA_OUTPUT_FILE="$(STATUS_SNAPSHOT_DELTA_OUTPUT_FILE)"
	@$(MAKE) --no-print-directory render-staging-governance-dashboard \
		WINDOW_ID="$(WINDOW_ID)" \
		STATUS_SNAPSHOT_HISTORY_DIR="$(STATUS_SNAPSHOT_HISTORY_DIR)" \
		WAR_ROOM_ACTION_PLAN_OUTPUT_FILE="$(WAR_ROOM_ACTION_PLAN_OUTPUT_FILE)" \
		STATUS_SNAPSHOT_MARKDOWN_OUTPUT_FILE="$(STATUS_SNAPSHOT_MARKDOWN_OUTPUT_FILE)" \
		STATUS_SNAPSHOT_DELTA_OUTPUT_FILE="$(STATUS_SNAPSHOT_DELTA_OUTPUT_FILE)" \
		GOVERNANCE_DASHBOARD_OUTPUT_FILE="$(GOVERNANCE_DASHBOARD_OUTPUT_FILE)"
	@$(MAKE) --no-print-directory render-staging-unblock-checklist \
		WINDOW_ID="$(WINDOW_ID)" \
		STATUS_SNAPSHOT_OUTPUT_FILE="$(STATUS_SNAPSHOT_OUTPUT_FILE)" \
		UNBLOCK_CHECKLIST_OUTPUT_FILE="$(UNBLOCK_CHECKLIST_OUTPUT_FILE)"
	@$(MAKE) --no-print-directory render-staging-comms-summary \
		WINDOW_ID="$(WINDOW_ID)" \
		STATUS_SNAPSHOT_OUTPUT_FILE="$(STATUS_SNAPSHOT_OUTPUT_FILE)" \
		STATUS_SNAPSHOT_DELTA_OUTPUT_FILE="$(STATUS_SNAPSHOT_DELTA_OUTPUT_FILE)" \
		GOVERNANCE_DASHBOARD_OUTPUT_FILE="$(GOVERNANCE_DASHBOARD_OUTPUT_FILE)" \
		UNBLOCK_CHECKLIST_OUTPUT_FILE="$(UNBLOCK_CHECKLIST_OUTPUT_FILE)" \
		COMMS_SUMMARY_OUTPUT_FILE="$(COMMS_SUMMARY_OUTPUT_FILE)"
	@$(MAKE) --no-print-directory render-staging-executive-bullet \
		WINDOW_ID="$(WINDOW_ID)" \
		STATUS_SNAPSHOT_OUTPUT_FILE="$(STATUS_SNAPSHOT_OUTPUT_FILE)" \
		STATUS_SNAPSHOT_DELTA_OUTPUT_FILE="$(STATUS_SNAPSHOT_DELTA_OUTPUT_FILE)" \
		EXECUTIVE_BULLET_OUTPUT_FILE="$(EXECUTIVE_BULLET_OUTPUT_FILE)"
	@$(MAKE) --no-print-directory render-staging-governance-consolidated-json \
		WINDOW_ID="$(WINDOW_ID)" \
		CHECKS_DIR="$(CHECKS_DIR)" \
		DOSSIERS_DIR="$(DOSSIERS_DIR)" \
		GOVERNANCE_WEEKLY_DIR="$(GOVERNANCE_WEEKLY_DIR)" \
		CONSOLIDATED_JSON_OUTPUT_FILE="$(CONSOLIDATED_JSON_OUTPUT_FILE)"
	@$(MAKE) --no-print-directory evaluate-governance-gate \
		CONSOLIDATED_JSON_OUTPUT_FILE="$(CONSOLIDATED_JSON_OUTPUT_FILE)" \
		GATE_POLICY="$(GATE_POLICY)" \
		GATE_OPERATION="$(GATE_OPERATION)"
	@if [ -n "$(SLACK_WEBHOOK_URL)" ] || [ -n "$$SLACK_WEBHOOK_URL" ]; then \
		$(MAKE) --no-print-directory notify-slack-governance \
			CONSOLIDATED_JSON_OUTPUT_FILE="$(CONSOLIDATED_JSON_OUTPUT_FILE)" \
			SLACK_WEBHOOK_URL="$(SLACK_WEBHOOK_URL)"; \
	fi

notify-slack-governance:
	@slack_webhook="$(SLACK_WEBHOOK_URL)"; \
	if [ -z "$$slack_webhook" ]; then \
		slack_webhook="$$SLACK_WEBHOOK_URL"; \
	fi; \
	if [ -z "$$slack_webhook" ]; then \
		echo "Error: SLACK_WEBHOOK_URL not set"; \
		exit 1; \
	fi; \
	$(PYTHON) scripts/notify_slack_governance.py \
		--consolidated-json "$(CONSOLIDATED_JSON_OUTPUT_FILE)" \
		--webhook-url "$$slack_webhook" \
		--channel governance \
		--mention-on-red

evaluate-governance-gate:
	@$(PYTHON) scripts/evaluate_governance_gate.py \
		--consolidated-json "$(CONSOLIDATED_JSON_OUTPUT_FILE)" \
		--gate-policy "$(GATE_POLICY)" \
		--operation "$(GATE_OPERATION)" \
		--format json

# Phase 7: Production Deployment & Monitoring

track-governance-history:
	@mkdir -p artifacts/deployment-history "$(GATE_ARTIFACTS_DIR)"
	@$(PYTHON) scripts/track_governance_history.py \
		--history-dir artifacts/deployment-history \
		--output-file "$(GATE_ARTIFACTS_DIR)/gate-history-metrics.json" \
		--generate-report

render-governance-gate-history-dashboard:
	@mkdir -p "$(GATE_ARTIFACTS_DIR)"
	@$(PYTHON) scripts/render_governance_gate_history_dashboard.py \
		--metrics-file "$(GATE_ARTIFACTS_DIR)/gate-history-metrics.json" \
		--output-file "$(GATE_ARTIFACTS_DIR)/gate-history-dashboard.md" \
		--include-trending

update-governance-metrics:
	@$(MAKE) --no-print-directory track-governance-history
	@$(MAKE) --no-print-directory render-governance-gate-history-dashboard

apply-regulatory-work-items-migration:
	@cat infra/postgres/migrations/0013_regulatory_work_items.sql | \
		docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U ontrackchain -d ontrackchain

apply-regulatory-work-items-contract-guardrails-migration:
	@cat infra/postgres/migrations/0014_regulatory_work_items_contract_guardrails.sql | \
		docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U ontrackchain -d ontrackchain

apply-evidence-package-seals-migration:
	@cat infra/postgres/migrations/0015_evidence_package_seals.sql | \
		docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U ontrackchain -d ontrackchain

apply-team-users-directory-migration:
	@cat infra/postgres/migrations/0016_team_users_directory.sql | \
		docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U ontrackchain -d ontrackchain

check-work-items-contracts:
	@python3 scripts/run_work_item_contract_suite.py

validate-work-items-runtime-local:
	@docker compose up -d postgres redis compliance-api
	@$(MAKE) --no-print-directory apply-regulatory-work-items-contract-guardrails-migration
	@$(MAKE) --no-print-directory smoke-work-items-ownership-backend

smoke-work-items-ownership-backend:
	@cat scripts/smoke_work_items_ownership_backend.py | docker compose exec -T compliance-api python -

# ================================
# PHASE 8: Enterprise Governance
# ================================

alert-pagerduty-governance-blocks:
	@$(PYTHON) scripts/alert_pagerduty_governance_blocks.py \
		--consolidated-json "$(GOVERNANCE_WEEKLY_DIR)/$(WINDOW_ID)-consolidated.json" \
		--severity error \
		--component production \
		--on-block

generate-environment-promotion-policy:
	@$(PYTHON) scripts/generate_environment_promotion_policy.py \
		--output-file docs/environment-promotion-policy.json \
		--include-rbac

generate-compliance-report:
	@$(PYTHON) scripts/generate_compliance_report.py \
		--metrics-file "$(GOVERNANCE_WEEKLY_DIR)/gate-history-metrics.json" \
		--output-file "docs/compliance-reports/compliance-report-$(shell date +%Y-%m-%d).md" \
		--period monthly \
		--format markdown

generate-compliance-reports-all:
	@$(MAKE) --no-print-directory generate-environment-promotion-policy
	@$(MAKE) --no-print-directory generate-compliance-report

# ================================
# PHASE 9: Auto Promotion
# ================================

evaluate-auto-promotion-readiness:
	@$(PYTHON) scripts/evaluate_auto_promotion_readiness.py \
		--metrics-file "$(GOVERNANCE_WEEKLY_DIR)/gate-history-metrics.json" \
		--environment staging \
		--min-allow-rate 85 \
		--max-override-rate 10 \
		--max-block-rate 15 \
		--min-total 10

check-workflow-hygiene:
	@$(PYTHON) -m unittest tests.test_check_workflow_hygiene
	@$(PYTHON) scripts/check_workflow_hygiene.py

prune-governance-weekly-archive:
	@$(PYTHON) scripts/prune_governance_weekly_archive.py \
		--days "$(GOVERNANCE_WEEKLY_ARCHIVE_RETENTION_DAYS)"

prune-governance-weekly-archive-dry-run:
	@$(PYTHON) scripts/prune_governance_weekly_archive.py \
		--days "$(GOVERNANCE_WEEKLY_ARCHIVE_RETENTION_DAYS)" \
		--dry-run
