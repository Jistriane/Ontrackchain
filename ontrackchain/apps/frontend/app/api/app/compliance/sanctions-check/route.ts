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
  const address = url.searchParams.get("address");
  const chain = url.searchParams.get("chain") ?? "ethereum";
  const lists = url.searchParams.get("lists") ?? "OFAC,UN,EU,COAF";

  if (!address) {
    return jsonResponse(JSON.stringify({ error: "missing_address" }), 422);
  }

  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik:8080";
  const res = await fetch(
    `${baseUrl}/api/v1/compliance/sanctions-check/${encodeURIComponent(address)}?chain=${encodeURIComponent(chain)}&lists=${encodeURIComponent(lists)}`,
    {
      method: "GET",
      headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
      cache: "no-store"
    }
  );

  return jsonResponse(await res.text(), res.status);
}
