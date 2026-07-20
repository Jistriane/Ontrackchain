import { cookies } from "next/headers";

export async function POST(request: Request) {

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify({ error: "not_authenticated" }), {
      status: 401,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const payload = await request.text();
  const res = await fetch(`${baseUrl}/api/v1/investigation/start`, {
    method: "POST",
    headers: { "content-type": "application/json", Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    body: payload,
    cache: "no-store"
  });

  const body = await res.text();
  return new Response(body || JSON.stringify({ detail: "investigation_operational_role_required" }), {
    status: res.status,
    headers: { "content-type": "application/json" }
  });
}
