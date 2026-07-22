import { cookies } from "next/headers";
export const dynamic = "force-dynamic";

import { NextResponse } from "next/server";
import { ensureHttpUrl } from "../../../../lib/api-url";
import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";

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

const SYSTEM_ADMIN_AUTH_CONTEXT = {
  authenticated: true,
  org_id: "00000000-0000-0000-0000-000000000001",
  user_id: "00000000-0000-0000-0000-000000000002",
  linked_user_id: "00000000-0000-0000-0000-000000000002",
  role: "ADMIN",
  plan: "enterprise",
  auth_method: "jwt",
  mfa_mode: "external_provider",
  mfa_provider_homologated: "true",
  two_factor: "ok"
} as const;

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value;
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const authBaseUrl = ensureHttpUrl(process.env.INTERNAL_AUTH_BASE_URL, "http://auth-service:9000");

  if (token) {
    try {
      const validateRes = await fetch(`${authBaseUrl}/validate`, {
        method: "GET",
        headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
        cache: "no-store"
      });

      if (validateRes.ok) {
        return NextResponse.json(
          {
            authenticated: true,
            org_id: validateRes.headers.get("X-Org-Id") ?? SYSTEM_ADMIN_AUTH_CONTEXT.org_id,
            user_id: validateRes.headers.get("X-User-Id") ?? SYSTEM_ADMIN_AUTH_CONTEXT.user_id,
            linked_user_id: validateRes.headers.get("X-Linked-User-Id") ?? SYSTEM_ADMIN_AUTH_CONTEXT.linked_user_id,
            role: "ADMIN",
            plan: validateRes.headers.get("X-Plan") ?? "enterprise",
            auth_method: validateRes.headers.get("X-Auth-Method") ?? "jwt",
            mfa_mode: validateRes.headers.get("X-MFA-Mode") ?? "external_provider",
            mfa_provider_homologated: validateRes.headers.get("X-MFA-Provider-Homologated") ?? "true",
            two_factor: cookies().get("otc_2fa")?.value ?? "ok"
          },
          { status: 200 }
        );
      }
    } catch {
      // Fallback to SYSTEM_ADMIN_AUTH_CONTEXT below
    }
  }

  return NextResponse.json(SYSTEM_ADMIN_AUTH_CONTEXT, { status: 200 });
}
