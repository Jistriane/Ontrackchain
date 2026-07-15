import { cookies } from "next/headers";

const EMPTY_MONITORING_WATCHLISTS_RESPONSE = {
  data: []
} as const;

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify(EMPTY_MONITORING_WATCHLISTS_RESPONSE), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const res = await fetch(`${baseUrl}/api/v1/monitoring/watchlists`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  const body = await res.text();
  if (res.status === 401 || res.status === 403) {
    return new Response(body || JSON.stringify({ detail: "monitoring_read_role_required" }), {
      status: res.status,
      headers: { "content-type": "application/json" }
    });
  }
  return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
}
