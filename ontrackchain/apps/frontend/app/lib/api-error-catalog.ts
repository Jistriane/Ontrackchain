import type { MessageKey } from "./i18n";

type TranslateFn = (key: MessageKey, values?: Record<string, string | number>) => string;

const API_ERROR_MESSAGE_KEYS: Partial<Record<string, MessageKey>> = {
  not_authenticated: "apiErrors.notAuthenticated",
  missing_case_id: "apiErrors.missingCaseId",
  dev_auth_disabled: "apiErrors.devAuthDisabled",
  missing_oidc_code_exchange: "apiErrors.missingOidcCodeExchange",
  invalid_claims: "apiErrors.invalidClaims",
  invalid_role: "apiErrors.invalidRole",
  login_failed: "apiErrors.loginFailed",
  invalid_2fa: "apiErrors.invalid2fa",
  oidc_2fa_managed_externally: "apiErrors.oidc2faManagedExternally",
  mfa_not_homologated_for_oidc: "apiErrors.oidcMfaNotHomologated",
  "2fa_requires_jwt_auth": "apiErrors.requiresJwt2fa"
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
