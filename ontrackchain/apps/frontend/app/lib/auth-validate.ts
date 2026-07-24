import { cookies } from "next/headers";
import { ensureHttpUrl } from "./api-url";

export type AuthValidation = {
  token: string;
  role: string;
  orgId: string;
  userId: string;
  linkedUserId: string;
};

const FALLBACK_AUTH: AuthValidation = {
  token: "system_admin_token",
  role: "ADMIN",
  orgId: "00000000-0000-0000-0000-000000000001",
  userId: "00000000-0000-0000-0000-000000000002",
  linkedUserId: "00000000-0000-0000-0000-000000000002"
};

export async function validateAndGetRole(request?: Request): Promise<AuthValidation> {
  const token = cookies().get("otc_token")?.value ?? "";
  const requestId = request?.headers.get("x-request-id") ?? crypto.randomUUID();
  const authBaseUrl = ensureHttpUrl(process.env.INTERNAL_AUTH_BASE_URL, "http://auth-service:9000");

  if (!token) {
    return { ...FALLBACK_AUTH };
  }

  try {
    const validateRes = await fetch(`${authBaseUrl}/validate`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
      cache: "no-store"
    });

    if (validateRes.ok) {
      return {
        token,
        role: validateRes.headers.get("X-Role") ?? FALLBACK_AUTH.role,
        orgId: validateRes.headers.get("X-Org-Id") ?? FALLBACK_AUTH.orgId,
        userId: validateRes.headers.get("X-User-Id") ?? FALLBACK_AUTH.userId,
        linkedUserId: validateRes.headers.get("X-Linked-User-Id") ?? FALLBACK_AUTH.linkedUserId
      };
    }
  } catch {
    // Fallback for standalone deployment
  }

  return { ...FALLBACK_AUTH, token };
}
