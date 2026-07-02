import { cookies } from "next/headers";

function jsonResponse(body: string, status: number) {
  return new Response(body, { status, headers: { "content-type": "application/json" } });
}

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return jsonResponse(JSON.stringify({ error: "not_authenticated" }), 401);
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const url = new URL(request.url);
  const query = url.search ? url.search : "";
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik:8080";
  const res = await fetch(`${baseUrl}/api/v1/compliance/counterparties${query}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  return jsonResponse(await res.text(), res.status);
}

export async function POST(request: Request) {
  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return jsonResponse(JSON.stringify({ error: "not_authenticated" }), 401);
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const payload = await request.text();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik:8080";
  const res = await fetch(`${baseUrl}/api/v1/compliance/counterparties`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Request-Id": requestId,
      "content-type": "application/json"
    },
    body: payload,
    cache: "no-store"
  });

  return jsonResponse(await res.text(), res.status);
}
