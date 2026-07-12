import { authenticateRequest, proxyOperationsRequest } from "../_shared";

const EMPTY_WORK_ITEMS = {
  data: [],
  page: 1,
  limit: 100,
  total: 0,
  has_more: false
} as const;

export async function GET(request: Request) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateRequest(requestId);
  if (auth instanceof Response) {
    return new Response(JSON.stringify(EMPTY_WORK_ITEMS), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const url = new URL(request.url);
  const query = url.search ? url.search : "";
  return proxyOperationsRequest(auth, {
    method: "GET",
    path: `/api/v1/operations/work-items${query}`,
    requestId
  });
}

export async function POST(request: Request) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  return proxyOperationsRequest(auth, {
    method: "POST",
    path: "/api/v1/operations/work-items",
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
}
