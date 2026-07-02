import { cookies } from "next/headers";

export async function POST(request: Request, context: { params: Promise<{ rosId: string }> }) {
  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify({ error: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const { rosId } = await context.params;
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const body = await request.text();
  const twofa = cookies().get("otc_2fa")?.value ?? "";
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik:8080";
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
  const res = await fetch(`${baseUrl}/api/v1/reports/ros-coaf/${rosId}/submitted`, {
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
      ...(twofa ? { "X-2FA": twofa } : {}),
      "content-type": "application/json"
    },
    body,
    cache: "no-store"
  });

  return new Response(await res.text(), { status: res.status, headers: { "content-type": "application/json" } });
}
