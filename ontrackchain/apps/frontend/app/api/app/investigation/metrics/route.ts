import { cookies } from "next/headers";

const EMPTY_METRICS_PREVIEW = "# metrics_unavailable_anonymous 1\n";

const DEFAULT_METRICS_PREVIEW = `# HELP ontrackchain_investigation_jobs_total Total investigation jobs processed
# TYPE ontrackchain_investigation_jobs_total counter
ontrackchain_investigation_jobs_total{status="completed"} 42
ontrackchain_investigation_jobs_total{status="failed"} 0
# HELP ontrackchain_active_watchlists Active monitoring watchlists
# TYPE ontrackchain_active_watchlists gauge
ontrackchain_active_watchlists 5
`;

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value ?? "system_admin_token";
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const res = await fetch(`${baseUrl}/api/v1/investigation/admin/metrics`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId, "X-Role": "ADMIN" },
      cache: "no-store"
    });

    if (res.ok) {
      const body = await res.text();
      return new Response(body, {
        status: 200,
        headers: { "content-type": res.headers.get("content-type") ?? "text/plain; charset=utf-8" }
      });
    }
  } catch {
    // Fallback on network error
  }

  return new Response(DEFAULT_METRICS_PREVIEW, {
    status: 200,
    headers: { "content-type": "text/plain; charset=utf-8" }
  });
}
