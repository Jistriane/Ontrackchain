import { cookies } from "next/headers";

const DEFAULT_PAGE = 1;
const DEFAULT_LIMIT = 20;

function buildEmptyCasesResponse(request: Request) {
  const url = new URL(request.url);
  const page = Number(url.searchParams.get("page") ?? DEFAULT_PAGE);
  const limit = Number(url.searchParams.get("limit") ?? DEFAULT_LIMIT);
  return {
    page: Number.isFinite(page) && page > 0 ? page : DEFAULT_PAGE,
    limit: Number.isFinite(limit) && limit > 0 ? limit : DEFAULT_LIMIT,
    data: []
  } as const;
}

export async function GET(request: Request) {

  const token = cookies().get("otc_token")?.value;
  if (!token) {
    return new Response(JSON.stringify(buildEmptyCasesResponse(request)), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const url = new URL(request.url);
  const query = url.search ? url.search : "";
  const baseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://traefik";
  const res = await fetch(`${baseUrl}/api/v1/investigation/history${query}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}`, "X-Request-Id": requestId },
    cache: "no-store"
  });

  if (res.status === 401 || res.status === 403) {
    return new Response(JSON.stringify(buildEmptyCasesResponse(request)), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const body = await res.text();
  return new Response(body, { status: res.status, headers: { "content-type": "application/json" } });
}
