import { cookies } from "next/headers";
import { isFrontendStandaloneShowcaseMode } from "../../../../../../lib/auth-runtime";
import { reviewStandaloneShowcaseCounterparty } from "../../../../../../lib/standalone-showcase";

function jsonResponse(body: string, status: number) {
  return new Response(body, { status, headers: { "content-type": "application/json" } });
}

export async function PATCH(request: Request, context: { params: Promise<{ counterpartyId: string }> }) {
  if (isFrontendStandaloneShowcaseMode()) {
    const { counterpartyId } = await context.params;
    const payload = (await request.json().catch(() => null)) as
      | {
          dd_review_status?: string | null;
          dd_review_note?: string | null;
          sof_description?: string | null;
          sof_document_ref?: string | null;
        }
      | null;
    const reviewed = reviewStandaloneShowcaseCounterparty(counterpartyId, payload ?? {});
    if (!reviewed) {
      return jsonResponse(JSON.stringify({ error: "counterparty_not_found" }), 404);
    }
    return jsonResponse(JSON.stringify(reviewed), 200);
  }

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return jsonResponse(JSON.stringify({ error: "not_authenticated" }), 401);
  }

  const { counterpartyId } = await context.params;
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const body = await request.text();
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
  const res = await fetch(`${baseUrl}/api/v1/compliance/counterparties/${counterpartyId}/review`, {
    method: "PATCH",
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
  return jsonResponse(responseBody || JSON.stringify({ detail: "counterparty_review_role_required" }), res.status);
}
