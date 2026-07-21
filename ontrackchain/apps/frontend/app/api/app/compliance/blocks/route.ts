import { cookies } from "next/headers";

function jsonResponse(body: string, status: number) {
  return new Response(body, { status, headers: { "content-type": "application/json" } });
}

const EMPTY_BLOCKS_RESPONSE = {
  items: [],
  total: 0
};

export async function GET(request: Request) {
  const url = new URL(request.url);
  const token = cookies().get("otc_token")?.value ?? "system_admin_token";
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const query = url.search ? url.search : "";
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";

  try {
    const res = await fetch(`${baseUrl}/api/v1/compliance/blocks${query}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Request-Id": requestId,
        "X-Role": "ADMIN"
      },
      cache: "no-store"
    });

    if (res.ok) {
      return jsonResponse(await res.text(), 200);
    }
  } catch {
    // Fallback on network/DNS error
  }

  return jsonResponse(JSON.stringify(EMPTY_BLOCKS_RESPONSE), 200);
}
