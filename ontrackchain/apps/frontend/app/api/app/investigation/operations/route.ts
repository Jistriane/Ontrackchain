import { validateAndGetRole } from "../../../../lib/auth-validate";
import { canReadInvestigationAdmin } from "../../../../lib/authz";
import { EMPTY_OPERATIONS_SNAPSHOT } from "../../../../lib/monitoring-investigation-operations";

const EMPTY_OPERATIONS_SNAPSHOT_RESPONSE = EMPTY_OPERATIONS_SNAPSHOT;

const PRIVILEGED_READ_DENIED = {
  detail: "privileged_read_role_required"
} as const;

export async function GET(request: Request) {
  const auth = await validateAndGetRole(request);
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();

  if (!canReadInvestigationAdmin(auth.role)) {
    return new Response(JSON.stringify(PRIVILEGED_READ_DENIED), {
      status: 403,
      headers: { "content-type": "application/json" }
    });
  }

  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const res = await fetch(`${baseUrl}/api/v1/investigation/admin/operations`, {
      method: "GET",
      headers: { Authorization: `Bearer ${auth.token}`, "X-Request-Id": requestId, "X-Role": auth.role },
      cache: "no-store"
    });

    if (res.ok || res.status === 403) {
      const body = await res.text();
      return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
    }
  } catch {
    // Fallback on network error
  }

  return new Response(JSON.stringify(EMPTY_OPERATIONS_SNAPSHOT_RESPONSE), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
