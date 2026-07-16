import { cookies } from "next/headers";
import { isFrontendStandaloneShowcaseMode } from "../../../../../../lib/auth-runtime";
import { acknowledgeStandaloneShowcasePlatformAlert } from "../../../../../../lib/standalone-showcase";

export async function POST(request: Request, context: { params: Promise<{ eventId: string }> }) {
  if (isFrontendStandaloneShowcaseMode()) {
    const { eventId } = await context.params;
    const payload = (await request.json().catch(() => null)) as { note?: string | null; triaged_by?: string | null } | null;
    const alert = acknowledgeStandaloneShowcasePlatformAlert(eventId, payload ?? {});
    if (!alert) {
      return new Response(JSON.stringify({ error: "platform_alert_not_found" }), {
        status: 404,
        headers: { "content-type": "application/json" }
      });
    }
    return new Response(JSON.stringify(alert), {
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

  const { eventId } = await context.params;
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const body = await request.text();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";
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
  const res = await fetch(`${baseUrl}/api/v1/monitoring/admin/operational-alerts/${eventId}/acknowledge`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Request-Id": requestId,
      "X-Role": role,
      ...(orgId ? { "X-Org-Id": orgId } : {}),
      ...(userId ? { "X-User-Id": userId } : {}),
      ...(linkedUserId ? { "X-Linked-User-Id": linkedUserId } : {}),
      "content-type": "application/json"
    },
    body,
    cache: "no-store"
  });

  const responseBody = await res.text();
  return new Response(responseBody, { status: res.status, headers: { "content-type": "application/json" } });
}
