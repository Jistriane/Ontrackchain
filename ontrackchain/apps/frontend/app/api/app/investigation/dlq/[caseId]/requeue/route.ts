import { cookies } from "next/headers";
import { ensureHttpUrl } from "../../../../../../lib/api-url";

type RouteContext = {
  params: Promise<{
    caseId: string;
  }>;
};

export async function POST(request: Request, context: RouteContext) {
  const token = cookies().get("otc_token")?.value ?? (request.headers.get("authorization")?.toLowerCase().startsWith("bearer ")
    ? request.headers.get("authorization")!.slice(7).trim()
    : "");

  if (!token) {
    return new Response(JSON.stringify({ error: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const { caseId } = await context.params;
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const authBaseUrl = ensureHttpUrl(process.env.INTERNAL_AUTH_BASE_URL, "http://auth-service:9000");
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

  const role = validateRes.headers.get("X-Role") ?? "ANALYST";
  const orgId = validateRes.headers.get("X-Org-Id");
  const userId = validateRes.headers.get("X-User-Id");
  const linkedUserId = validateRes.headers.get("X-Linked-User-Id");

  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const payload = await request.text();
  const res = await fetch(`${baseUrl}/api/v1/investigation/admin/dlq/${caseId}/requeue`, {
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

  const body = await res.text();
  return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
}
