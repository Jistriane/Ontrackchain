import { cookies } from "next/headers";

const EMPTY_METRICS_PREVIEW = "# metrics_unavailable_anonymous 1\n";

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(EMPTY_METRICS_PREVIEW, {
      status: 200,
      headers: { "content-type": "text/plain; charset=utf-8" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik:8080";
  const res = await fetch(`${baseUrl}/api/v1/investigation/admin/metrics`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (res.status === 401 || res.status === 403) {
    return new Response(EMPTY_METRICS_PREVIEW, {
      status: 200,
      headers: { "content-type": "text/plain; charset=utf-8" }
    });
  }

  const body = await res.text();
  return new Response(body, {
    status: res.status,
    headers: { "content-type": res.headers.get("content-type") ?? "text/plain; charset=utf-8" }
  });
}
