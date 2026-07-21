import { cookies } from "next/headers";

const EMPTY_PLATFORM_OPERATIONAL_ALERTS = {
  status_filter: null,
  triage_status_filter: null,
  service_filter: null,
  receiver_filter: null,
  severity_filter: null,
  cursor: null,
  limit: 20,
  total_count: 0,
  count: 0,
  has_more: false,
  next_cursor: null,
  data: []
} as const;

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value ?? "system_admin_token";
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const url = new URL(request.url);
  const query = url.search ? url.search : "";
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";

  let orgId = "00000000-0000-0000-0000-000000000001";
  let userId = "00000000-0000-0000-0000-000000000002";
  let linkedUserId = "00000000-0000-0000-0000-000000000002";
  let role = "ADMIN";

  try {
    const validateRes = await fetch(`${authBaseUrl}/validate`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
      cache: "no-store"
    });

    if (validateRes.ok) {
      orgId = validateRes.headers.get("X-Org-Id") ?? orgId;
      userId = validateRes.headers.get("X-User-Id") ?? userId;
      linkedUserId = validateRes.headers.get("X-Linked-User-Id") ?? linkedUserId;
      role = "ADMIN";
    }
  } catch {
    // Fallback for standalone deployment
  }

  try {
    const res = await fetch(`${baseUrl}/api/v1/monitoring/admin/operational-alerts${query}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Request-Id": requestId,
        "X-Role": role,
        "X-Org-Id": orgId,
        "X-User-Id": userId,
        "X-Linked-User-Id": linkedUserId
      },
      cache: "no-store"
    });

    const body = await res.text();
    return new Response(body || JSON.stringify(EMPTY_PLATFORM_OPERATIONAL_ALERTS), {
      status: res.status,
      headers: { "content-type": "application/json" }
    });
  } catch {
    return new Response(JSON.stringify(EMPTY_PLATFORM_OPERATIONAL_ALERTS), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }
}
