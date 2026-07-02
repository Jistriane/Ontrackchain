import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return NextResponse.json({ error: "not_authenticated" }, { status: 401 });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";
  const validateRes = await fetch(`${authBaseUrl}/validate`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (!validateRes.ok) {
    return NextResponse.json({ error: "not_authenticated" }, { status: 401 });
  }

  return NextResponse.json(
    {
      org_id: validateRes.headers.get("X-Org-Id"),
      user_id: validateRes.headers.get("X-User-Id"),
      linked_user_id: validateRes.headers.get("X-Linked-User-Id"),
      role: validateRes.headers.get("X-Role"),
      plan: validateRes.headers.get("X-Plan"),
      auth_method: validateRes.headers.get("X-Auth-Method"),
      mfa_mode: validateRes.headers.get("X-MFA-Mode"),
      mfa_provider_homologated: validateRes.headers.get("X-MFA-Provider-Homologated")
    },
    { status: 200 }
  );
}

