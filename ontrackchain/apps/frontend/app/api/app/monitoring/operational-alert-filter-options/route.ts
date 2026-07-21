import { cookies } from "next/headers";

const EMPTY_PLATFORM_ALERT_FILTER_OPTIONS = {
  services: [],
  receivers: [],
  generated_at: new Date(0).toISOString()
} as const;

const DEFAULT_PLATFORM_ALERT_FILTER_OPTIONS = {
  services: ["auth-service", "compliance-api", "investigation-api", "report-api", "monitoring-api"],
  receivers: ["coaf_channel", "internal_slack", "email_auditor", "webhook_default"],
  generated_at: new Date().toISOString()
} as const;

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value ?? "system_admin_token";
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const res = await fetch(`${baseUrl}/api/v1/monitoring/admin/operational-alerts/filter-options`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Request-Id": requestId,
        "X-Role": "ADMIN"
      },
      cache: "no-store"
    });

    if (res.ok) {
      const body = await res.text();
      return new Response(body, { status: 200, headers: { "content-type": "application/json" } });
    }
  } catch {
    // Fallback gracefully on DNS/network error
  }

  return new Response(JSON.stringify(DEFAULT_PLATFORM_ALERT_FILTER_OPTIONS), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
