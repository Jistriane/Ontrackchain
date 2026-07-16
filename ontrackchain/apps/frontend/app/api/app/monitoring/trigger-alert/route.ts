import { cookies } from "next/headers";
import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import { createStandaloneShowcaseMonitoringAlert } from "../../../../lib/standalone-showcase";

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = (await request.json().catch(() => null)) as
      | {
          watchlist_id?: string;
          address?: string;
          chain?: string;
          severity?: string;
          title?: string;
          details?: Record<string, unknown>;
        }
      | null;
    if (!payload?.watchlist_id?.trim() || !payload.address?.trim() || !payload.chain?.trim()) {
      return new Response(JSON.stringify({ error: "invalid_trigger_alert_payload" }), {
        status: 422,
        headers: { "content-type": "application/json" }
      });
    }
    return new Response(JSON.stringify(createStandaloneShowcaseMonitoringAlert({
      watchlist_id: payload.watchlist_id,
      address: payload.address,
      chain: payload.chain,
      severity: payload.severity,
      title: payload.title,
      details: payload.details
    })), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify({ error: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";
  const payload = await request.text();
  const validateRes = await fetch(`${authBaseUrl}/validate`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (!validateRes.ok) {
    return new Response(JSON.stringify({ error: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const orgId = validateRes.headers.get("X-Org-Id");
  const userId = validateRes.headers.get("X-User-Id");
  const linkedUserId = validateRes.headers.get("X-Linked-User-Id");
  const role = validateRes.headers.get("X-Role") ?? "ANALYST";
  const res = await fetch(`${baseUrl}/api/v1/monitoring/test/trigger-alert`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Request-Id": requestId,
      "X-Role": role,
      ...(orgId ? { "X-Org-Id": orgId } : {}),
      ...(userId ? { "X-User-Id": userId } : {}),
      ...(linkedUserId ? { "X-Linked-User-Id": linkedUserId } : {})
    },
    body: payload,
    cache: "no-store"
  });

  const body = await res.text();
  return new Response(body || JSON.stringify({ detail: "monitoring_test_trigger_role_required" }), {
    status: res.status,
    headers: { "content-type": "application/json" }
  });
}
