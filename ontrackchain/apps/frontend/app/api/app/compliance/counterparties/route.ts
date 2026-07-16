import { cookies } from "next/headers";
import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import {
  createStandaloneShowcaseCounterparty,
  listStandaloneShowcaseCounterparties
} from "../../../../lib/standalone-showcase";

function jsonResponse(body: string, status: number) {
  return new Response(body, { status, headers: { "content-type": "application/json" } });
}

const EMPTY_COUNTERPARTY_LIST_RESPONSE = {
  items: [],
  total: 0
} as const;

export async function GET(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const url = new URL(request.url);
    return jsonResponse(
      JSON.stringify(
        listStandaloneShowcaseCounterparties({
          limit: Number(url.searchParams.get("limit") ?? 20),
          offset: Number(url.searchParams.get("offset") ?? 0)
        })
      ),
      200
    );
  }

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return jsonResponse(JSON.stringify(EMPTY_COUNTERPARTY_LIST_RESPONSE), 200);
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const url = new URL(request.url);
  const query = url.search ? url.search : "";
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";
  const validateRes = await fetch(`${authBaseUrl}/validate`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (!validateRes.ok) {
    return jsonResponse(JSON.stringify({ error: "not_authenticated" }), 401);
  }

  const orgId = validateRes.headers.get("X-Org-Id");
  const userId = validateRes.headers.get("X-User-Id");
  const linkedUserId = validateRes.headers.get("X-Linked-User-Id");
  const role = validateRes.headers.get("X-Role") ?? "VIEWER";
  const res = await fetch(`${baseUrl}/api/v1/compliance/counterparties${query}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Request-Id": requestId,
      "X-Role": role,
      ...(orgId ? { "X-Org-Id": orgId } : {}),
      ...(userId ? { "X-User-Id": userId } : {}),
      ...(linkedUserId ? { "X-Linked-User-Id": linkedUserId } : {})
    },
    cache: "no-store"
  });

  const responseBody = await res.text();
  return jsonResponse(responseBody || JSON.stringify({ detail: "counterparty_read_role_required" }), res.status);
}

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = (await request.json().catch(() => null)) as
      | {
          counterparty_type?: string | null;
          legal_name?: string | null;
          document_type?: string | null;
          document_number?: string | null;
          wallet_addresses?: Array<{ chain?: string | null; address?: string | null; label?: string | null }> | null;
          declared_risk_context?: string | null;
          onchain_risk_score?: number | null;
        }
      | null;
    const created = createStandaloneShowcaseCounterparty(payload ?? {});
    if (!created) {
      return jsonResponse(JSON.stringify({ error: "invalid_counterparty_payload" }), 422);
    }
    return jsonResponse(JSON.stringify(created), 200);
  }

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return jsonResponse(JSON.stringify({ error: "not_authenticated" }), 401);
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const payload = await request.text();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";
  const validateRes = await fetch(`${authBaseUrl}/validate`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (!validateRes.ok) {
    return jsonResponse(JSON.stringify({ error: "not_authenticated" }), 401);
  }

  const orgId = validateRes.headers.get("X-Org-Id");
  const userId = validateRes.headers.get("X-User-Id");
  const linkedUserId = validateRes.headers.get("X-Linked-User-Id");
  const role = validateRes.headers.get("X-Role") ?? "ANALYST";
  const res = await fetch(`${baseUrl}/api/v1/compliance/counterparties`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Request-Id": requestId,
      "X-Role": role,
      ...(orgId ? { "X-Org-Id": orgId } : {}),
      ...(userId ? { "X-User-Id": userId } : {}),
      ...(linkedUserId ? { "X-Linked-User-Id": linkedUserId } : {}),
      "content-type": "application/json"
    },
    body: payload,
    cache: "no-store"
  });

  return jsonResponse(await res.text(), res.status);
}
