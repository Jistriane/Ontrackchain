import { NextResponse } from "next/server";

import {
  isDevAuthEnabled,
  isFrontendStandaloneShowcaseMode,
  resolveAppEnv,
  resolveConfiguredAuthMode,
  resolveEffectiveAuthMode
} from "../../lib/auth-runtime";

import { ensureHttpUrl } from "../../lib/api-url";

function readTrimmed(value: string | undefined) {
  const normalized = value?.trim();
  return normalized ? normalized : null;
}

function readBoolean(value: string | undefined) {
  const normalized = value?.trim().toLowerCase();
  if (!normalized) {
    return null;
  }
  if (["1", "true", "yes", "on"].includes(normalized)) {
    return true;
  }
  if (["0", "false", "no", "off"].includes(normalized)) {
    return false;
  }
  return null;
}

function readNumber(value: string | undefined) {
  if (!value?.trim()) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function deriveTokenUrl(env: NodeJS.ProcessEnv) {
  const explicitFromEnv = readTrimmed(env.OIDC_TOKEN_URL);
  if (explicitFromEnv) {
    return explicitFromEnv;
  }

  const issuerUrl = readTrimmed(env.OIDC_ISSUER_URL);
  if (issuerUrl) {
    return `${issuerUrl.replace(/\/+$/, "")}/protocol/openid-connect/token`;
  }

  const authorizationUrl = readTrimmed(env.OIDC_AUTHORIZATION_URL);
  if (!authorizationUrl) {
    return null;
  }

  try {
    const url = new URL(authorizationUrl);
    url.pathname = url.pathname.replace(/\/protocol\/openid-connect\/auth\/?$/, "/protocol/openid-connect/token");
    url.search = "";
    url.hash = "";
    return url.toString();
  } catch {
    return null;
  }
}

function resolveOidcProvider(env: NodeJS.ProcessEnv) {
  return readTrimmed(env.OIDC_PROVIDER) ?? "keycloak";
}

function resolveOidcClaimNames(env: NodeJS.ProcessEnv) {
  const provider = resolveOidcProvider(env).toLowerCase();
  const defaultsByProvider: Record<string, { org: string; plan: string; role: string }> = {
    generic: { org: "org_id", plan: "plan", role: "role" },
    keycloak: { org: "org", plan: "plan", role: "otk_role" },
    auth0: { org: "org_id", plan: "plan", role: "role" },
    entra: { org: "tenant_id", plan: "extension_plan", role: "roles" }
  };
  const defaults = defaultsByProvider[provider] ?? defaultsByProvider.keycloak;

  return {
    org: readTrimmed(env.OIDC_ORG_CLAIM) ?? defaults.org,
    plan: readTrimmed(env.OIDC_PLAN_CLAIM) ?? defaults.plan,
    role: readTrimmed(env.OIDC_ROLE_CLAIM) ?? defaults.role
  };
}

function buildFallbackConfig(env: NodeJS.ProcessEnv = process.env) {
  const appEnv = resolveAppEnv(env);
  const authMode = resolveConfiguredAuthMode(env);
  const effectiveAuthMode = resolveEffectiveAuthMode(env);
  const devAuthEnabled = isDevAuthEnabled(env);
  const oidcProvider = resolveOidcProvider(env);
  const oidcClaims = resolveOidcClaimNames(env);

  return {
    auth_mode: authMode,
    effective_auth_mode: effectiveAuthMode,
    app_env: appEnv,
    dev_auth_enabled: devAuthEnabled,
    mfa: {
      enabled: effectiveAuthMode === "oidc",
      method: effectiveAuthMode === "oidc" ? "external_provider" : "totp",
      managed_by: effectiveAuthMode === "oidc" ? "oidc_provider" : "application",
      provider: oidcProvider,
      provider_homologated: readBoolean(env.MFA_EXTERNAL_PROVIDER_HOMOLOGATED),
      issuer: readTrimmed(env.MFA_TOTP_ISSUER),
      account_name: readTrimmed(env.MFA_TOTP_ACCOUNT_NAME),
      period_seconds: readNumber(env.MFA_TOTP_PERIOD_SECONDS),
      digits: readNumber(env.MFA_TOTP_DIGITS)
    },
    oidc: {
      enabled: effectiveAuthMode === "oidc",
      provider: oidcProvider,
      issuer_url: readTrimmed(env.OIDC_ISSUER_URL),
      client_id: readTrimmed(env.OIDC_CLIENT_ID),
      audience: readTrimmed(env.OIDC_AUDIENCE),
      authorization_url: readTrimmed(env.OIDC_AUTHORIZATION_URL),
      token_url: deriveTokenUrl(env),
      claims: oidcClaims
    }
  };
}

export async function GET(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    return NextResponse.json({
      auth_mode: "dev",
      effective_auth_mode: "dev",
      app_env: resolveAppEnv(),
      dev_auth_enabled: true,
      mfa: {
        enabled: true,
        method: "external_provider",
        managed_by: "showcase",
        provider: "showcase",
        provider_homologated: true,
        issuer: "OnTrackChain Showcase",
        account_name: "showcase-user@ontrackchain",
        period_seconds: 30,
        digits: 6
      },
      oidc: {
        enabled: false,
        provider: null,
        issuer_url: null,
        client_id: null,
        audience: null,
        authorization_url: null,
        token_url: null
      }
    });
  }

  const rawAuthBaseUrl = readTrimmed(process.env.INTERNAL_AUTH_BASE_URL);
  const authBaseUrl = rawAuthBaseUrl ? ensureHttpUrl(rawAuthBaseUrl, "") : "";
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();

  if (authBaseUrl) {
    try {
      const upstreamResponse = await fetch(`${authBaseUrl}/auth/config`, {
        headers: { "X-Request-Id": requestId },
        cache: "no-store"
      });
      if (upstreamResponse.ok) {
        const payload = await upstreamResponse.json().catch(() => null);
        if (payload) {
          return NextResponse.json(payload, { status: upstreamResponse.status });
        }
      }
    } catch {
      // Fallback below keeps the login bootstrap functional even under partial env drift.
    }
  }

  return NextResponse.json(buildFallbackConfig(), { status: 200 });
}
