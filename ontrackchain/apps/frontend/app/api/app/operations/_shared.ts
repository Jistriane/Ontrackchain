import { cookies } from "next/headers";

type AuthContext = {
  token: string;
  orgId: string | null;
  userId: string | null;
  linkedUserId: string | null;
  role: string;
  mfaMode: string | null;
  mfaProviderHomologated: string | null;
  twoFactor: string | null;
};

type ProxyRequestOptions = {
  method: string;
  path: string;
  requestId: string;
  body?: string;
  contentType?: string;
};

export function jsonResponse(body: string, status: number) {
  return new Response(body, { status, headers: { "content-type": "application/json" } });
}

export async function authenticateRequest(requestId: string): Promise<AuthContext | Response> {

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return jsonResponse(JSON.stringify({ error: "not_authenticated" }), 401);
  }

  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";
  const validateRes = await fetch(`${authBaseUrl}/validate`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (!validateRes.ok) {
    return jsonResponse(JSON.stringify({ error: "not_authenticated" }), 401);
  }

  return {
    token,
    orgId: validateRes.headers.get("X-Org-Id"),
    userId: validateRes.headers.get("X-User-Id"),
    linkedUserId: validateRes.headers.get("X-Linked-User-Id"),
    role: validateRes.headers.get("X-Role") ?? "ANALYST",
    mfaMode: validateRes.headers.get("X-MFA-Mode"),
    mfaProviderHomologated: validateRes.headers.get("X-MFA-Provider-Homologated"),
    twoFactor: validateRes.headers.get("X-2FA")
  };
}

export async function proxyOperationsRequest(auth: AuthContext, options: ProxyRequestOptions) {
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const res = await fetch(`${baseUrl}${options.path}`, {
    method: options.method,
    headers: {
      Authorization: `Bearer ${auth.token}`,
      "X-Request-Id": options.requestId,
      "X-Role": auth.role,
      ...(auth.orgId ? { "X-Org-Id": auth.orgId } : {}),
      ...(auth.userId ? { "X-User-Id": auth.userId } : {}),
      ...(auth.linkedUserId ? { "X-Linked-User-Id": auth.linkedUserId } : {}),
      ...(auth.mfaMode ? { "X-MFA-Mode": auth.mfaMode } : {}),
      ...(auth.mfaProviderHomologated ? { "X-MFA-Provider-Homologated": auth.mfaProviderHomologated } : {}),
      ...(auth.twoFactor ? { "X-2FA": auth.twoFactor } : {}),
      ...(options.contentType ? { "content-type": options.contentType } : {})
    },
    body: options.body,
    cache: "no-store"
  });

  return jsonResponse(await res.text(), res.status);
}
