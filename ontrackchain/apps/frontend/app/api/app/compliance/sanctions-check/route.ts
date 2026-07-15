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

  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";
  const validateRes = await fetch(`${authBaseUrl}/validate`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (!validateRes.ok) {
    return jsonResponse(JSON.stringify({ error: "not_authenticated" }), 401);
  }

  const orgId = validateRes.headers.get("X-Org-Id");
  const userId = validateRes.headers.get("X-User-Id");
  const linkedUserId = validateRes.headers.get("X-Linked-User-Id");
  const role = validateRes.headers.get("X-Role") ?? "VIEWER";
  const res = await fetch(
    `${baseUrl}/api/v1/compliance/sanctions-check/${encodeURIComponent(address)}?chain=${encodeURIComponent(chain)}&lists=${encodeURIComponent(lists)}`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Request-Id": requestId,
        "X-Role": role,
        ...(orgId ? { "X-Org-Id": orgId } : {}),
        ...(userId ? { "X-User-Id": userId } : {}),
        ...(linkedUserId ? { "X-Linked-User-Id": linkedUserId } : {})
      },
      cache: "no-store"
    }
  );

  const responseBody = await res.text();
  return jsonResponse(responseBody || JSON.stringify({ detail: "sanctions_check_role_required" }), res.status);
}
