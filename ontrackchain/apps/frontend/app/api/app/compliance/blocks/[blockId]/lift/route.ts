import { cookies } from "next/headers";
import { isFrontendStandaloneShowcaseMode } from "../../../../../../lib/auth-runtime";
import { liftStandaloneShowcaseBlock } from "../../../../../../lib/standalone-showcase";

export async function POST(request: Request, context: { params: Promise<{ blockId: string }> }) {
  const { blockId } = await context.params;
  const body = await request.text();
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = JSON.parse(body || "{}") as { reason?: string | null };
    const lifted = liftStandaloneShowcaseBlock(blockId, payload);
    if (!lifted) {
      return new Response(JSON.stringify({ error: "block_not_found" }), {
        status: 404,
        headers: { "content-type": "application/json" }
      });
    }
    return new Response(JSON.stringify(lifted), {
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
  const mfaMode = validateRes.headers.get("X-MFA-Mode");
  const mfaProviderHomologated = validateRes.headers.get("X-MFA-Provider-Homologated");
  const res = await fetch(`${baseUrl}/api/v1/compliance/blocks/${blockId}/lift`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Request-Id": requestId,
      "X-Role": role,
      ...(orgId ? { "X-Org-Id": orgId } : {}),
      ...(userId ? { "X-User-Id": userId } : {}),
      ...(linkedUserId ? { "X-Linked-User-Id": linkedUserId } : {}),
      ...(mfaMode ? { "X-MFA-Mode": mfaMode } : {}),
      ...(mfaProviderHomologated ? { "X-MFA-Provider-Homologated": mfaProviderHomologated } : {}),
      "content-type": "application/json"
    },
    body,
    cache: "no-store"
  });

  const responseBody = await res.text();
  return new Response(responseBody || JSON.stringify({ detail: "block_lift_role_required" }), {
    status: res.status,
    headers: { "content-type": "application/json" }
  });
}
