import { ensureHttpUrl } from "../../../lib/api-url";
export const dynamic = "force-dynamic";

type MockTokenResponse = {
  access_token?: string;
};

export async function POST(request: Request) {
  const authBaseUrl = ensureHttpUrl(process.env.INTERNAL_AUTH_BASE_URL, "http://auth-service:9000");
  const internalOidcBaseUrl = ensureHttpUrl(process.env.INTERNAL_OIDC_BASE_URL, "http://mock-oidc:9101");
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const body = (await request.json().catch(() => ({}))) as {
    role?: string;
    org?: string;
    plan?: string;
    sub?: string;
  };

  const role = (body.role ?? "").trim().toUpperCase();
  if (!role) {
    return new Response(JSON.stringify({ error: "missing_role" }), {
      status: 400,
      headers: { "content-type": "application/json" }
    });
  }

  const configRes = await fetch(`${authBaseUrl}/auth/config`, {
    headers: { "X-Request-Id": requestId },
    cache: "no-store"
  });
  if (!configRes.ok) {
    return new Response(JSON.stringify({ error: "auth_config_unavailable" }), {
      status: 503,
      headers: { "content-type": "application/json" }
    });
  }
  const config = (await configRes.json().catch(() => null)) as any;
  const provider = String(config?.oidc?.provider ?? "").toLowerCase();
  if (provider !== "mock") {
    return new Response(JSON.stringify({ error: "mock_oidc_disabled" }), {
      status: 409,
      headers: { "content-type": "application/json" }
    });
  }

  const tokenRes = await fetch(`${internalOidcBaseUrl}/mock/token`, {
    method: "POST",
    headers: { "content-type": "application/json", "X-Request-Id": requestId },
    body: JSON.stringify({
      role,
      org: body.org,
      plan: body.plan,
      sub: body.sub
    }),
    cache: "no-store"
  });

  if (!tokenRes.ok) {
    return new Response(JSON.stringify({ error: "token_issue_failed" }), {
      status: 502,
      headers: { "content-type": "application/json" }
    });
  }

  const tokenBody = (await tokenRes.json().catch(() => null)) as MockTokenResponse | null;
  if (!tokenBody?.access_token?.trim()) {
    return new Response(JSON.stringify({ error: "token_issue_failed" }), {
      status: 502,
      headers: { "content-type": "application/json" }
    });
  }

  return new Response(JSON.stringify({ access_token: tokenBody.access_token }), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
