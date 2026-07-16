import { cookies } from "next/headers";
import { isFrontendStandaloneShowcaseMode } from "../../../../../lib/auth-runtime";
import { evaluateStandaloneShowcaseBlock } from "../../../../../lib/standalone-showcase";

export async function POST(request: Request) {
  const body = await request.text();
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = JSON.parse(body || "{}") as {
      address?: string | null;
      chain?: string | null;
      entity_name?: string | null;
      entity_document?: string | null;
    };
    if (!payload.address?.trim()) {
      return new Response(JSON.stringify({ error: "missing_address" }), {
        status: 422,
        headers: { "content-type": "application/json" }
      });
    }
    return new Response(JSON.stringify(evaluateStandaloneShowcaseBlock(payload as { address: string; chain?: string | null; entity_name?: string | null; entity_document?: string | null })), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify({ error: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";
  const validateRes = await fetch(`${authBaseUrl}/validate`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (!validateRes.ok) {
    return new Response(JSON.stringify({ error: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const orgId = validateRes.headers.get("X-Org-Id");
  const userId = validateRes.headers.get("X-User-Id");
  const linkedUserId = validateRes.headers.get("X-Linked-User-Id");
  const role = validateRes.headers.get("X-Role") ?? "ANALYST";
  const res = await fetch(`${baseUrl}/api/v1/compliance/blocks/evaluate`, {
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
    body,
    cache: "no-store"
  });

  const responseBody = await res.text();
  return new Response(responseBody || JSON.stringify({ detail: "block_evaluate_role_required" }), {
    status: res.status,
    headers: { "content-type": "application/json" }
  });
}
