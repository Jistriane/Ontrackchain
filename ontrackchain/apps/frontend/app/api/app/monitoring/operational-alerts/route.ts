import { validateAndGetRole } from "../../../../lib/auth-validate";
import { canReadMonitoringAdmin } from "../../../../lib/authz";

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

const MONITORING_READ_DENIED = {
  detail: "monitoring_read_role_required"
} as const;

export async function GET(request: Request) {
  const auth = await validateAndGetRole(request);
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();

  if (!canReadMonitoringAdmin(auth.role)) {
    return new Response(JSON.stringify(MONITORING_READ_DENIED), {
      status: 403,
      headers: { "content-type": "application/json" }
    });
  }

  const url = new URL(request.url);
  const query = url.search ? url.search : "";
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const res = await fetch(`${baseUrl}/api/v1/monitoring/admin/operational-alerts${query}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${auth.token}`,
        "X-Request-Id": requestId,
        "X-Role": auth.role,
        "X-Org-Id": auth.orgId,
        "X-User-Id": auth.userId,
        "X-Linked-User-Id": auth.linkedUserId
      },
      cache: "no-store"
    });

    if (res.ok || res.status === 403) {
      const body = await res.text();
      return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
    }
  } catch {
    // Fallback for standalone deployment
  }

  return new Response(JSON.stringify(EMPTY_PLATFORM_OPERATIONAL_ALERTS), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
