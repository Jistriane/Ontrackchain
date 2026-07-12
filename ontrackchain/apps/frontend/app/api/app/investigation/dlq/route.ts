import { cookies } from "next/headers";

const DEFAULT_DLQ_LIMIT = 100;

function buildEmptyDlqResponse(request: Request) {
  const url = new URL(request.url);
  const state = url.searchParams.get("state")?.trim() || "failed_permanent";
  const targetChain = url.searchParams.get("target_chain")?.trim() || null;
  const limit = Number(url.searchParams.get("limit") ?? DEFAULT_DLQ_LIMIT);

  return {
    count: 0,
    credits_available: 0,
    filters: {
      state,
      target_chain: targetChain,
      can_requeue: null,
      limit: Number.isFinite(limit) && limit > 0 ? limit : DEFAULT_DLQ_LIMIT
    },
    cases: [],
    generated_at: ""
  } as const;
}

export async function GET(request: Request) {
  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify(buildEmptyDlqResponse(request)), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const url = new URL(request.url);
  const query = url.search ? url.search : "";
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik:8080";
  const res = await fetch(`${baseUrl}/api/v1/investigation/admin/dlq${query}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (res.status === 401 || res.status === 403) {
    return new Response(JSON.stringify(buildEmptyDlqResponse(request)), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const body = await res.text();
  return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
}
