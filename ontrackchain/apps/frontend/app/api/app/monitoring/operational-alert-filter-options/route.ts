import { cookies } from "next/headers";

const EMPTY_PLATFORM_ALERT_FILTER_OPTIONS = {
  services: [],
  receivers: [],
  generated_at: new Date(0).toISOString()
} as const;

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify(EMPTY_PLATFORM_ALERT_FILTER_OPTIONS), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik:8080";
  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";
  const validateRes = await fetch(`${authBaseUrl}/validate`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (!validateRes.ok) {
    return new Response(JSON.stringify(EMPTY_PLATFORM_ALERT_FILTER_OPTIONS), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const orgId = validateRes.headers.get("X-Org-Id");
  const userId = validateRes.headers.get("X-User-Id");
  const linkedUserId = validateRes.headers.get("X-Linked-User-Id");
  const role = validateRes.headers.get("X-Role") ?? "ANALYST";
  const res = await fetch(`${baseUrl}/api/v1/monitoring/admin/operational-alerts/filter-options`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Request-Id": requestId,
      "X-Role": role,
      ...(orgId ? { "X-Org-Id": orgId } : {}),
      ...(userId ? { "X-User-Id": userId } : {}),
      ...(linkedUserId ? { "X-Linked-User-Id": linkedUserId } : {})
    },
    cache: "no-store"
  });

  if (res.status === 401 || res.status === 403) {
    return new Response(JSON.stringify(EMPTY_PLATFORM_ALERT_FILTER_OPTIONS), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const body = await res.text();
  return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
}
