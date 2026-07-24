import { validateAndGetRole } from "../../../../lib/auth-validate";
export const dynamic = "force-dynamic";


const EMPTY_BILLING_BALANCE_RESPONSE = {
  credits_available: 0,
  credits_reserved: 0,
  credits_used_total: 0
} as const;

const DEFAULT_BILLING_BALANCE = {
  credits_available: 10000,
  credits_reserved: 0,
  credits_used_total: 250
} as const;

export async function GET(request: Request) {
  const auth = await validateAndGetRole(request);
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const res = await fetch(`${baseUrl}/api/v1/billing/balance`, {
      method: "GET",
      headers: { Authorization: `Bearer ${auth.token}`, "X-Request-Id": requestId, "X-Role": auth.role },
      cache: "no-store"
    });

    if (res.ok || res.status === 403) {
      const body = await res.text();
      return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
    }
  } catch {
    // Fallback on network error
  }

  return new Response(JSON.stringify(DEFAULT_BILLING_BALANCE), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
