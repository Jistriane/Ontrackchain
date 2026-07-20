import { cookies } from "next/headers";

export async function GET(request: Request) {

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify({ error: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const url = new URL(request.url);
  const limit = url.searchParams.get("limit");
  const targetUrl = new URL(`${baseUrl}/api/v1/billing/reconciliation/export`);
  if (limit) {
    targetUrl.searchParams.set("limit", limit);
  }

  const res = await fetch(targetUrl, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  const responseBody = await res.arrayBuffer();
  const contentType = res.headers.get("content-type") ?? "application/json";
  const contentDisposition = res.headers.get("content-disposition");
  return new Response(responseBody, {
    status: res.status,
    headers: contentDisposition
      ? { "content-type": contentType, "content-disposition": contentDisposition }
      : { "content-type": contentType }
  });
}
