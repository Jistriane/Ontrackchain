import { cookies } from "next/headers";

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

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify({ detail: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const url = new URL(request.url);
  const query = url.search ? url.search : "";

  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const res = await fetch(`${baseUrl}/api/v1/audit/logs${query}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (res.status === 401 || res.status === 403) {
    const body = await res.text();
    return new Response(body || JSON.stringify({ detail: "privileged_read_role_required" }), {
      status: res.status,
      headers: { "content-type": "application/json" }
    });
  }

  const body = await res.text();
  return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
}
