import { validateAndGetRole } from "../../../../lib/auth-validate";
import { canReadBilling } from "../../../../lib/authz";

const EMPTY_BILLING_RECONCILIATION_RESPONSE = {
  generated_at: new Date(0).toISOString(),
  balance: {
    credits_available: 0,
    credits_reserved: 0,
    credits_used_total: 0
  },
  quotes: {
    investigation: { open_total: 0, expired_total: 0 },
    compliance: { open_total: 0, expired_total: 0 },
    monitoring: { open_total: 0, expired_total: 0 },
    open_total: 0,
    expired_total: 0
  },
  ledger: {
    total_entries: 0,
    action_totals: [],
    recent: []
  }
} as const;

const BILLING_RECONCILIATION_DENIED = {
  detail: "billing_reconciliation_role_required"
} as const;

export async function GET(request: Request) {
  const auth = await validateAndGetRole(request);
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();

  if (!canReadBilling(auth.role)) {
    return new Response(JSON.stringify(BILLING_RECONCILIATION_DENIED), {
      status: 403,
      headers: { "content-type": "application/json" }
    });
  }

  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const url = new URL(request.url);
  const limit = url.searchParams.get("limit");
  const targetUrl = new URL(`${baseUrl}/api/v1/billing/reconciliation`);
  if (limit) {
    targetUrl.searchParams.set("limit", limit);
  }

  try {
    const res = await fetch(targetUrl, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${auth.token}`,
        "X-Request-Id": requestId,
        "X-Role": auth.role
      },
      cache: "no-store"
    });

    if (res.ok || res.status === 403) {
      const body = await res.text();
      return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
    }
  } catch {
    // Fallback on network error
  }

  return new Response(JSON.stringify(EMPTY_BILLING_RECONCILIATION_RESPONSE), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
