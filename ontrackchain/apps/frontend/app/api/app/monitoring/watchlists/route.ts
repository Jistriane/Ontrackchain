import { cookies } from "next/headers";

const EMPTY_MONITORING_WATCHLISTS_RESPONSE = {
  data: []
} as const;

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value ?? "system_admin_token";
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const res = await fetch(`${baseUrl}/api/v1/monitoring/watchlists`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId, "X-Role": "ADMIN" },
      cache: "no-store"
    });

    const body = await res.text();
    if (res.ok) {
      return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
    }
  } catch {
    // Fallback on network error
  }

  return new Response(JSON.stringify(EMPTY_MONITORING_WATCHLISTS_RESPONSE), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
