import { cookies } from "next/headers";

const EMPTY_BILLING_BALANCE_RESPONSE = {
  credits_available: 0,
  credits_reserved: 0,
  credits_used_total: 0
} as const;

export async function GET(request: Request) {

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify(EMPTY_BILLING_BALANCE_RESPONSE), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const res = await fetch(`${baseUrl}/api/v1/billing/balance`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (res.status === 401 || res.status === 403) {
    const body = await res.text();
    return new Response(body || JSON.stringify({ detail: "billing_balance_role_required" }), {
      status: res.status,
      headers: { "content-type": "application/json" }
    });
  }

  const body = await res.text();
  return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
}
