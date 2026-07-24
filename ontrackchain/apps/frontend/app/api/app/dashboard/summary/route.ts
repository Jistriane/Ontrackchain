import { validateAndGetRole } from "../../../../lib/auth-validate";
export const dynamic = "force-dynamic";

const DEFAULT_DASHBOARD_SUMMARY = {
  total_cases: 0,
  active_cases: 0,
  total_alerts: 0,
  open_alerts: 0,
  total_counterparties: 0,
  blocked_counterparties: 0,
  total_sanctions_checks: 0,
  pending_reviews: 0,
  revenue: 0
} as const;

export async function GET(request: Request) {
  const auth = await validateAndGetRole(request);
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const res = await fetch(`${baseUrl}/api/v1/dashboard/summary`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${auth.token}`,
        "X-Request-Id": requestId,
        "X-Role": auth.role,
        "X-Org-Id": auth.orgId,
        "X-User-Id": auth.userId
      },
      cache: "no-store"
    });

    if (res.ok || res.status === 403) {
      const body = await res.text();
      return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
    }
  } catch {
    // Fallback on network error
  }

  return new Response(JSON.stringify(DEFAULT_DASHBOARD_SUMMARY), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
