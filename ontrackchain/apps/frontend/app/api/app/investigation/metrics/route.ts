import { validateAndGetRole } from "../../../../lib/auth-validate";
import { canReadInvestigationAdmin } from "../../../../lib/authz";

const EMPTY_METRICS_PREVIEW = "# metrics_unavailable_anonymous 1\n";

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
    const res = await fetch(`${baseUrl}/api/v1/investigation/admin/metrics`, {
      method: "GET",
      headers: { Authorization: `Bearer ${auth.token}`, "X-Request-Id": requestId, "X-Role": auth.role },
      cache: "no-store"
    });

    if (res.ok || res.status === 403) {
      const body = await res.text();
      return new Response(body, {
        status: res.status,
        headers: { "content-type": res.headers.get("content-type") ?? "text/plain; charset=utf-8" }
      });
    }
  } catch {
    // Fallback on network error
  }

  return new Response(EMPTY_METRICS_PREVIEW, {
    status: 200,
    headers: { "content-type": "text/plain; charset=utf-8" }
  });
}
