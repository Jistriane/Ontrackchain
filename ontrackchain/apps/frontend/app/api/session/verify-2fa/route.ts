import { cookies } from "next/headers";

import {
  isConfiguredDevAuthButDisabled,
  isFrontendStandaloneShowcaseMode,
  resolveEffectiveAuthMode
} from "../../../lib/auth-runtime";

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    cookies().set("otc_2fa", "managed_externally_homologated", { httpOnly: true, sameSite: "lax", path: "/" });
    return new Response(JSON.stringify({ status: "ok", mode: "standalone_showcase" }), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  if (isConfiguredDevAuthButDisabled()) {
    return new Response(JSON.stringify({ error: "dev_auth_disabled" }), {
      status: 503,
      headers: { "content-type": "application/json" }
    });
  }

  const authMode = resolveEffectiveAuthMode();
  if (authMode === "oidc") {
    return new Response(JSON.stringify({ error: "oidc_2fa_managed_externally" }), {
      status: 400,
      headers: { "content-type": "application/json" }
    });
  }

  const body = (await request.json()) as { code?: string };
  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify({ error: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";
  const res = await fetch(`${authBaseUrl}/auth/verify-2fa`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Request-Id": requestId,
      "content-type": "application/json"
    },
    body: JSON.stringify(body),
    cache: "no-store"
  });
  if (!res.ok) {
    const errorBody = await res.text();
    return new Response(errorBody || JSON.stringify({ error: "invalid_2fa" }), {
      status: res.status,
      headers: { "content-type": "application/json" }
    });
  }

  cookies().set("otc_2fa", "ok", { httpOnly: true, sameSite: "lax", path: "/" });
  const responseBody = await res.text();
  return new Response(responseBody || JSON.stringify({ status: "ok" }), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
