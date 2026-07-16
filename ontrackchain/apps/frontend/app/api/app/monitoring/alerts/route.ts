import { cookies } from "next/headers";
import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import { listStandaloneShowcaseMonitoringAlerts } from "../../../../lib/standalone-showcase";

export async function GET(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const url = new URL(request.url);
    return new Response(
      JSON.stringify(
        listStandaloneShowcaseMonitoringAlerts({
          watchlistId: url.searchParams.get("watchlist_id"),
          limit: Number(url.searchParams.get("limit") ?? 50)
        })
      ),
      {
        status: 200,
        headers: { "content-type": "application/json" }
      }
    );
  }

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify({ error: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const url = new URL(request.url);
  const query = url.search ? url.search : "";

  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const res = await fetch(`${baseUrl}/api/v1/monitoring/alerts${query}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  const body = await res.text();
  return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
}
