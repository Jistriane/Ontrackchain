import { cookies } from "next/headers";

const EMPTY_OPERATIONAL_ALERTS_RESPONSE = {
  generated_at: new Date(0).toISOString(),
  open_total: 0,
  critical_open_total: 0,
  alerts: []
} as const;

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value ?? "system_admin_token";
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const res = await fetch(`${baseUrl}/api/v1/investigation/admin/alerts`, {
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
    // Fallback for offline/unreachable backend
  }

  return new Response(JSON.stringify(EMPTY_OPERATIONAL_ALERTS_RESPONSE), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
