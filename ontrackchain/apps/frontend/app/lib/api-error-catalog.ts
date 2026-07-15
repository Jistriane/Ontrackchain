import type { MessageKey } from "./i18n";

type TranslateFn = (key: MessageKey, values?: Record<string, string | number>) => string;

const API_ERROR_MESSAGE_KEYS: Partial<Record<string, MessageKey>> = {
  not_authenticated: "apiErrors.notAuthenticated",
  missing_address: "apiErrors.missingAddress",
  missing_case_id: "apiErrors.missingCaseId",
  missing_org_context: "apiErrors.missingOrgContext",
  missing_user_context: "apiErrors.missingUserContext",
  "2fa_required": "apiErrors.twoFactorRequired",
  dev_auth_disabled: "apiErrors.devAuthDisabled",
  missing_oidc_code_exchange: "apiErrors.missingOidcCodeExchange",
  invalid_claims: "apiErrors.invalidClaims",
  invalid_role: "apiErrors.invalidRole",
  login_failed: "apiErrors.loginFailed",
  invalid_2fa: "apiErrors.invalid2fa",
  oidc_2fa_managed_externally: "apiErrors.oidc2faManagedExternally",
  mfa_not_homologated_for_oidc: "apiErrors.oidcMfaNotHomologated",
  "2fa_requires_jwt_auth": "apiErrors.requiresJwt2fa",
  linked_user_required_for_counterparty_creation: "apiErrors.linkedUserRequiredForCounterpartyCreation",
  counterparty_read_role_required: "apiErrors.counterpartyReadRoleRequired",
  counterparty_create_role_required: "apiErrors.counterpartyCreateRoleRequired",
  sanctions_check_role_required: "apiErrors.sanctionsCheckRoleRequired",
  block_evaluate_role_required: "apiErrors.blockEvaluateRoleRequired",
  counterparty_review_role_required: "apiErrors.counterpartyReviewRoleRequired",
  linked_user_required_for_block_lift: "apiErrors.linkedUserRequiredForBlockLift",
  block_lift_role_required: "apiErrors.blockLiftRoleRequired",
  mfa_external_provider_required: "apiErrors.mfaExternalProviderRequired",
  mfa_provider_not_homologated: "apiErrors.mfaProviderNotHomologated",
  monitoring_test_trigger_role_required: "apiErrors.monitoringTestTriggerRoleRequired",
  investigation_operational_role_required: "apiErrors.investigationOperationalRoleRequired",
  billing_balance_role_required: "apiErrors.billingBalanceRoleRequired",
  billing_reconciliation_role_required: "apiErrors.billingReconciliationRoleRequired",
  billing_export_role_required: "apiErrors.billingExportRoleRequired",
  coaf_report_requires_compliance_officer: "apiErrors.coafRequiresComplianceOfficer",
  coaf_report_review_role_required: "apiErrors.coafReviewRoleRequired",
  coaf_report_submission_role_required: "apiErrors.coafSubmissionRoleRequired",
  report_write_role_required: "apiErrors.reportWriteRoleRequired",
  report_detail_role_required: "apiErrors.reportDetailRoleRequired",
  report_download_role_required: "apiErrors.reportDownloadRoleRequired",
  report_formal_dossier_role_required: "apiErrors.reportFormalDossierRoleRequired",
  legal_report_requires_jwt_auth: "apiErrors.legalReportRequiresJwtAuth",
  legal_report_requires_admin_role: "apiErrors.legalReportRequiresAdminRole",
  coaf_report_requires_external_provider_mfa: "apiErrors.coafRequiresExternalMfa",
  coaf_report_requires_homologated_provider: "apiErrors.coafRequiresHomologatedProvider",
  linked_user_required_for_coaf_report: "apiErrors.linkedUserRequiredForCoafReport",
  team_user_create_role_required: "apiErrors.teamUserCreateRoleRequired",
  team_user_update_role_required: "apiErrors.teamUserUpdateRoleRequired",
  team_user_disable_role_required: "apiErrors.teamUserDisableRoleRequired",
  team_federated_identity_read_role_required: "apiErrors.teamFederatedIdentityReadRoleRequired",
  team_external_identity_already_linked: "apiErrors.teamExternalIdentityAlreadyLinked",
  team_federated_identity_link_role_required: "apiErrors.teamFederatedIdentityLinkRoleRequired",
  team_federated_identity_unlink_role_required: "apiErrors.teamFederatedIdentityUnlinkRoleRequired",
  team_federated_directory_search_role_required: "apiErrors.teamFederatedDirectorySearchRoleRequired",
  team_federated_directory_suggestion_role_required: "apiErrors.teamFederatedDirectorySuggestionRoleRequired",
  team_external_identity_not_found: "apiErrors.teamExternalIdentityNotFound",
  team_external_identity_provider_required: "apiErrors.teamExternalIdentityProviderRequired",
  team_external_identity_provider_invalid: "apiErrors.teamExternalIdentityProviderInvalid",
  team_external_identity_subject_required: "apiErrors.teamExternalIdentitySubjectRequired",
  federated_directory_query_required: "apiErrors.federatedDirectoryQueryRequired",
  federated_directory_limit_invalid: "apiErrors.federatedDirectoryLimitInvalid",
  federated_directory_unavailable: "apiErrors.federatedDirectoryUnavailable",
  federated_directory_forbidden: "apiErrors.federatedDirectoryForbidden",
  federated_directory_candidate_not_found: "apiErrors.federatedDirectoryCandidateNotFound",
  missing_keycloak_admin_base_url: "apiErrors.federatedDirectoryNotConfigured",
  missing_keycloak_admin_client_id: "apiErrors.federatedDirectoryNotConfigured",
  missing_keycloak_admin_client_secret: "apiErrors.federatedDirectoryNotConfigured",
  missing_keycloak_admin_realm: "apiErrors.federatedDirectoryNotConfigured",
  ros_record_not_found: "apiErrors.rosRecordNotFound",
  ros_record_not_pending_approval: "apiErrors.rosRecordNotPendingApproval",
  ros_record_not_approved: "apiErrors.rosRecordNotApproved",
  rejection_reason_required: "apiErrors.rejectionReasonRequired",
  coaf_protocol_number_required: "apiErrors.coafProtocolNumberRequired",
  coaf_receipt_hash_must_be_sha256: "apiErrors.coafReceiptHashMustBeSha256",
  unsupported_chain: "apiErrors.unsupportedChain",
  privileged_read_role_required: "apiErrors.privilegedReadRoleRequired",
  privileged_write_role_required: "apiErrors.privilegedWriteRoleRequired",
  manual_package_seal_not_found: "apiErrors.manualPackageSealNotFound",
  manual_package_seal_locked: "apiErrors.manualPackageSealLocked",
  manual_package_signoff_role_already_recorded: "apiErrors.manualPackageSignoffRoleAlreadyRecorded",
  manual_package_seal_not_ready: "apiErrors.manualPackageSealNotReady",
  manual_package_signoff_incomplete: "apiErrors.manualPackageSignoffIncomplete",
  manual_seal_secret_missing: "apiErrors.manualSealSecretMissing",
  manual_package_seal_already_revoked: "apiErrors.manualPackageSealAlreadyRevoked",
  manual_package_seal_already_superseded: "apiErrors.manualPackageSealAlreadySuperseded",
  manual_package_seal_revoked: "apiErrors.manualPackageSealRevoked",
  manual_package_supersede_target_invalid: "apiErrors.manualPackageSupersedeTargetInvalid",
  manual_package_supersede_target_not_sealed: "apiErrors.manualPackageSupersedeTargetNotSealed",
  manual_package_supersede_target_revoked: "apiErrors.manualPackageSupersedeTargetRevoked",
  manual_package_supersede_target_superseded: "apiErrors.manualPackageSupersedeTargetSuperseded"
};

export function extractApiErrorCode(payload: unknown): string | null {
  if (typeof payload === "string" && payload.trim()) {
    return payload.trim();
  }

  if (payload && typeof payload === "object") {
    const candidate = payload as { error?: unknown; detail?: unknown };
    if (typeof candidate.error === "string" && candidate.error.trim()) {
      return candidate.error.trim();
    }
    if (typeof candidate.detail === "string" && candidate.detail.trim()) {
      return candidate.detail.trim();
    }
    if (candidate.detail && typeof candidate.detail === "object") {
      const nested = candidate.detail as { error?: unknown };
      if (typeof nested.error === "string" && nested.error.trim()) {
        return nested.error.trim();
      }
    }
  }

  return null;
}

export function resolveApiErrorMessage(t: TranslateFn, payload: unknown, fallback: string): string {
  const errorCode = extractApiErrorCode(payload);
  if (!errorCode) {
    return fallback;
  }

  const messageKey = API_ERROR_MESSAGE_KEYS[errorCode];
  return messageKey ? t(messageKey) : errorCode;
}
