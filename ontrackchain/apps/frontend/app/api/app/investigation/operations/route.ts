import { cookies } from "next/headers";
import { EMPTY_OPERATIONS_SNAPSHOT } from "../../../../lib/monitoring-investigation-operations";

const EMPTY_OPERATIONS_SNAPSHOT_RESPONSE = EMPTY_OPERATIONS_SNAPSHOT;

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify(EMPTY_OPERATIONS_SNAPSHOT_RESPONSE), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const res = await fetch(`${baseUrl}/api/v1/investigation/admin/operations`, {
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
