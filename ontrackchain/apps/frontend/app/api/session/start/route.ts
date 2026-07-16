import { cookies } from "next/headers";

import {
  isConfiguredDevAuthButDisabled,
  isFrontendStandaloneShowcaseMode,
  resolveEffectiveAuthMode
} from "../../../lib/auth-runtime";

type AuthConfigResponse = {
  mfa?: {
    provider_homologated?: boolean;
  };
  oidc?: {
    client_id?: string | null;
    token_url?: string | null;
  };
};

type TokenExchangeResponse = {
  access_token?: string;
  error?: string;
  error_description?: string;
};

type ValidateErrorResponse = {
  detail?: string;
};

async function loadOidcConfig(authBaseUrl: string, requestId: string): Promise<AuthConfigResponse | null> {
  const configRes = await fetch(`${authBaseUrl}/auth/config`, {
    headers: { "X-Request-Id": requestId },
    cache: "no-store"
  });
  if (!configRes.ok) {
    return null;
  }
  return (await configRes.json()) as AuthConfigResponse;
}

async function exchangeAuthorizationCode(params: {
  authBaseUrl: string;
  code: string;
  codeVerifier: string;
  redirectUri: string;
  requestId: string;
}): Promise<string | null> {
  const config = await loadOidcConfig(params.authBaseUrl, params.requestId);
  const clientId = config?.oidc?.client_id?.trim();
  const tokenUrl = config?.oidc?.token_url?.trim();
  if (!clientId || !tokenUrl) {
    return null;
  }
  const tokenEndpoint = resolveServerSideTokenUrl(tokenUrl);

  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: clientId,
    code: params.code,
    code_verifier: params.codeVerifier,
    redirect_uri: params.redirectUri
  });
  const tokenRes = await fetch(tokenEndpoint, {
    method: "POST",
    headers: {
      "content-type": "application/x-www-form-urlencoded",
      "X-Request-Id": params.requestId
    },
    body: body.toString(),
    cache: "no-store"
  });
  if (!tokenRes.ok) {
    return null;
  }

  const tokenBody = (await tokenRes.json().catch(() => null)) as TokenExchangeResponse | null;
  return tokenBody?.access_token?.trim() || null;
}

function resolveServerSideTokenUrl(publicTokenUrl: string): string {
  const internalKeycloakBaseUrl = process.env.INTERNAL_KEYCLOAK_BASE_URL?.trim();
  if (!internalKeycloakBaseUrl) {
    return publicTokenUrl;
  }
  try {
    const url = new URL(publicTokenUrl);
    const internalBase = new URL(internalKeycloakBaseUrl);
    url.protocol = internalBase.protocol;
    url.host = internalBase.host;
    return url.toString();
  } catch {
    return publicTokenUrl;
  }
}

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const body = (await request.json().catch(() => null)) as { role?: string; plan?: string } | null;
    cookies().set("otc_token", "standalone-showcase", { httpOnly: true, sameSite: "lax", path: "/" });
    cookies().set("otc_2fa", "managed_externally_homologated", { httpOnly: true, sameSite: "lax", path: "/" });
    return new Response(
      JSON.stringify({
        require2fa: false,
        authMode: "dev",
        role: (body?.role ?? "ADMIN").trim().toUpperCase(),
        plan: body?.plan ?? "enterprise",
        mode: "standalone_showcase"
      }),
      {
        status: 200,
        headers: { "content-type": "application/json" }
      }
    );
  }

  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";
  const authMode = resolveEffectiveAuthMode();
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const body = (await request.json()) as {
    code?: string;
    codeVerifier?: string;
    plan?: string;
    redirectUri?: string;
    role?: string;
    token?: string;
  };
  const plan = body.plan ?? "professional";
  const role = (body.role ?? "ADMIN").trim().toUpperCase();
  const allowedRoles = new Set(["ADMIN", "AUDITOR", "ANALYST"]);

  if (isConfiguredDevAuthButDisabled()) {
    return new Response(JSON.stringify({ error: "dev_auth_disabled" }), {
      status: 503,
      headers: { "content-type": "application/json" }
    });
  }

  if (authMode === "oidc") {
    const config = await loadOidcConfig(authBaseUrl, requestId);
    let token = body.token?.trim();
    const code = body.code?.trim();
    const codeVerifier = body.codeVerifier?.trim();
    const redirectUri = body.redirectUri?.trim();

    if (!token && code && codeVerifier && redirectUri) {
      const exchangedToken = await exchangeAuthorizationCode({
        authBaseUrl,
        code,
        codeVerifier,
        redirectUri,
        requestId
      });
      if (exchangedToken) {
        token = exchangedToken;
      }
    }

    if (!token) {
      return new Response(JSON.stringify({ error: "missing_oidc_code_exchange" }), {
        status: 401,
        headers: { "content-type": "application/json" }
      });
    }

    const validateRes = await fetch(`${authBaseUrl}/validate`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
      cache: "no-store"
    });

    if (!validateRes.ok) {
      const validateError = (await validateRes.json().catch(() => null)) as ValidateErrorResponse | null;
      const exposedError = validateError?.detail === "invalid_claims" ? "invalid_claims" : "login_failed";
      return new Response(JSON.stringify({ error: exposedError }), {
        status: 401,
        headers: { "content-type": "application/json" }
      });
    }

    cookies().set("otc_token", token, { httpOnly: true, sameSite: "lax", path: "/" });
    cookies().set("otc_2fa", config?.mfa?.provider_homologated ? "managed_externally_homologated" : "managed_externally", {
      httpOnly: true,
      sameSite: "lax",
      path: "/"
    });
    return new Response(JSON.stringify({ require2fa: false, authMode }), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  if (!allowedRoles.has(role)) {
    return new Response(JSON.stringify({ error: "invalid_role" }), {
      status: 400,
      headers: { "content-type": "application/json" }
    });
  }

  const orgId = "00000000-0000-0000-0000-000000000001";
  const userId = "00000000-0000-0000-0000-000000000002";

  const res = await fetch(`${baseUrl}/auth/issue-dev-token`, {
    method: "POST",
    headers: { "content-type": "application/json", "X-Request-Id": requestId },
    body: JSON.stringify({ org_id: orgId, user_id: userId, plan, role, expires_in_minutes: 60 }),
    cache: "no-store"
  });

  if (!res.ok) {
    return new Response(JSON.stringify({ error: "login_failed" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const data = (await res.json()) as { token: string };
  cookies().set("otc_token", data.token, { httpOnly: true, sameSite: "lax", path: "/" });
  cookies().set("otc_2fa", "pending", { httpOnly: true, sameSite: "lax", path: "/" });

  return new Response(JSON.stringify({ require2fa: true, authMode }), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
