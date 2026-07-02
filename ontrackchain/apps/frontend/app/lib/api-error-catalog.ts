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
  linked_user_required_for_block_lift: "apiErrors.linkedUserRequiredForBlockLift",
  mfa_external_provider_required: "apiErrors.mfaExternalProviderRequired",
  mfa_provider_not_homologated: "apiErrors.mfaProviderNotHomologated",
  coaf_report_requires_compliance_officer: "apiErrors.coafRequiresComplianceOfficer",
  coaf_report_requires_external_provider_mfa: "apiErrors.coafRequiresExternalMfa",
  coaf_report_requires_homologated_provider: "apiErrors.coafRequiresHomologatedProvider",
  linked_user_required_for_coaf_report: "apiErrors.linkedUserRequiredForCoafReport",
  ros_record_not_found: "apiErrors.rosRecordNotFound",
  ros_record_not_pending_approval: "apiErrors.rosRecordNotPendingApproval",
  ros_record_not_approved: "apiErrors.rosRecordNotApproved",
  rejection_reason_required: "apiErrors.rejectionReasonRequired",
  coaf_protocol_number_required: "apiErrors.coafProtocolNumberRequired",
  coaf_receipt_hash_must_be_sha256: "apiErrors.coafReceiptHashMustBeSha256",
  unsupported_chain: "apiErrors.unsupportedChain"
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
