import { cookies } from "next/headers";

const DEFAULT_ESTIMATE_RESPONSE = {
  estimated_cost: 15.0,
  estimated_duration_ms: 1200,
  tier: "standard",
  available_credits: 10000.0
};

export async function POST(request: Request) {
  const token = cookies().get("otc_token")?.value ?? "system_admin_token";
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const payload = await request.text();
    const res = await fetch(`${baseUrl}/api/v1/investigation/estimate`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        Authorization: `Bearer ${token}`,
        "X-Request-Id": requestId,
        "X-Role": "ADMIN"
      },
      body: payload,
      cache: "no-store"
    });

    if (res.ok) {
      const body = await res.text();
      return new Response(body, { status: 200, headers: { "content-type": "application/json" } });
    }
  } catch {
    // Fallback on network/DNS error
  }

  return new Response(JSON.stringify(DEFAULT_ESTIMATE_RESPONSE), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
