import { cookies } from "next/headers";
import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import { getStandaloneShowcaseBillingReconciliation } from "../../../../lib/standalone-showcase";

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

export async function GET(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const url = new URL(request.url);
    return new Response(
      JSON.stringify(getStandaloneShowcaseBillingReconciliation(Number(url.searchParams.get("limit") ?? 5))),
      {
        status: 200,
        headers: { "content-type": "application/json" }
      }
    );
  }

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify(EMPTY_BILLING_RECONCILIATION_RESPONSE), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const url = new URL(request.url);
  const limit = url.searchParams.get("limit");
  const targetUrl = new URL(`${baseUrl}/api/v1/billing/reconciliation`);
  if (limit) {
    targetUrl.searchParams.set("limit", limit);
  }

  const res = await fetch(targetUrl, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (res.status === 401 || res.status === 403) {
    const body = await res.text();
    return new Response(body || JSON.stringify({ detail: "billing_reconciliation_role_required" }), {
      status: res.status,
      headers: { "content-type": "application/json" }
    });
  }

  const body = await res.text();
  return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
}
