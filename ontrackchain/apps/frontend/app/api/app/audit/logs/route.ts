import { validateAndGetRole } from "../../../../lib/auth-validate";

const EMPTY_AUDIT_LOGS_RESPONSE = {
  data: [],
  page: 1,
  count: 0,
  limit: 50,
  total: 0,
  total_pages: 1,
  has_more: false
} as const;

export async function GET(request: Request) {
  const auth = await validateAndGetRole(request);
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const url = new URL(request.url);
  const query = url.search ? url.search : "";

  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const res = await fetch(`${baseUrl}/api/v1/audit/logs${query}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${auth.token}`, "X-Request-Id": requestId, "X-Role": auth.role },
      cache: "no-store"
    });

    const body = await res.text();
    if (res.ok || res.status === 403) {
      return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
    }
  } catch {
    // Fallback on network error
  }

  return new Response(JSON.stringify(EMPTY_AUDIT_LOGS_RESPONSE), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
