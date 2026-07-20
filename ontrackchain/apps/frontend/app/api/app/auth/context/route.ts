import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { ensureHttpUrl } from "../../../../lib/api-url";

const ANONYMOUS_AUTH_CONTEXT = {
  authenticated: false,
  org_id: null,
  user_id: null,
  linked_user_id: null,
  role: null,
  plan: null,
  auth_method: null,
  mfa_mode: null,
  mfa_provider_homologated: null,
  two_factor: null
} as const;

export async function GET(request: Request) {

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return NextResponse.json(ANONYMOUS_AUTH_CONTEXT, { status: 200 });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const authBaseUrl = ensureHttpUrl(process.env.INTERNAL_AUTH_BASE_URL, "http://auth-service:9000");
  const validateRes = await fetch(`${authBaseUrl}/validate`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (!validateRes.ok) {
    return NextResponse.json(ANONYMOUS_AUTH_CONTEXT, { status: 200 });
  }

  return NextResponse.json(
    {
      authenticated: true,
      org_id: validateRes.headers.get("X-Org-Id"),
      user_id: validateRes.headers.get("X-User-Id"),
      linked_user_id: validateRes.headers.get("X-Linked-User-Id"),
      role: validateRes.headers.get("X-Role"),
      plan: validateRes.headers.get("X-Plan"),
      auth_method: validateRes.headers.get("X-Auth-Method"),
      mfa_mode: validateRes.headers.get("X-MFA-Mode"),
      mfa_provider_homologated: validateRes.headers.get("X-MFA-Provider-Homologated"),
      two_factor: cookies().get("otc_2fa")?.value ?? validateRes.headers.get("X-2FA")
    },
    { status: 200 }
  );
}
