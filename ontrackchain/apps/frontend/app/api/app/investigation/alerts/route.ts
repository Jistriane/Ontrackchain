import { cookies } from "next/headers";
import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import { getStandaloneShowcaseInvestigationOperationalAlerts } from "../../../../lib/standalone-showcase";

const EMPTY_OPERATIONAL_ALERTS_RESPONSE = {
  generated_at: new Date(0).toISOString(),
  open_total: 0,
  critical_open_total: 0,
  alerts: []
} as const;

export async function GET(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    return new Response(JSON.stringify(getStandaloneShowcaseInvestigationOperationalAlerts()), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify(EMPTY_OPERATIONAL_ALERTS_RESPONSE), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const res = await fetch(`${baseUrl}/api/v1/investigation/admin/alerts`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (res.status === 401 || res.status === 403) {
    const body = await res.text();
    return new Response(body || JSON.stringify({ detail: "privileged_read_role_required" }), {
      status: res.status,
      headers: { "content-type": "application/json" }
    });
  }

  const body = await res.text();
  return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
}
