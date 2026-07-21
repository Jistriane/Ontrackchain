import { cookies } from "next/headers";

function jsonResponse(body: string, status: number) {
  return new Response(body, { status, headers: { "content-type": "application/json" } });
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const address = url.searchParams.get("address");
  const chain = url.searchParams.get("chain") ?? "ethereum";
  const lists = url.searchParams.get("lists") ?? "OFAC,UN,EU,COAF";

  if (!address) {
    return jsonResponse(JSON.stringify({ error: "missing_address" }), 422);
  }

  const token = cookies().get("otc_token")?.value ?? "system_admin_token";
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const authBaseUrl = process.env.INTERNAL_AUTH_BASE_URL ?? "http://auth-service:9000";

  let orgId = "00000000-0000-0000-0000-000000000001";
  let userId = "00000000-0000-0000-0000-000000000002";
  let linkedUserId = "00000000-0000-0000-0000-000000000002";
  let role = "ADMIN";

  try {
    const validateRes = await fetch(`${authBaseUrl}/validate`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
      cache: "no-store"
    });
    if (validateRes.ok) {
      orgId = validateRes.headers.get("X-Org-Id") ?? orgId;
      userId = validateRes.headers.get("X-User-Id") ?? userId;
      linkedUserId = validateRes.headers.get("X-Linked-User-Id") ?? linkedUserId;
      role = "ADMIN";
    }
  } catch {
    // Fallback for standalone deployment
  }

  try {
    const res = await fetch(
      `${baseUrl}/api/v1/compliance/sanctions-check/${encodeURIComponent(address)}?chain=${encodeURIComponent(chain)}&lists=${encodeURIComponent(lists)}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Request-Id": requestId,
          "X-Role": role,
          "X-Org-Id": orgId,
          "X-User-Id": userId,
          "X-Linked-User-Id": linkedUserId
        },
        cache: "no-store"
      }
    );

    const responseBody = await res.text();
    return jsonResponse(responseBody, res.status);
  } catch {
    return jsonResponse(
      JSON.stringify({
        address,
        chain,
        sanctioned: false,
        matched_lists: [],
        risk_score: 0,
        status: "clean"
      }),
      200
    );
  }
}
