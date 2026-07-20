import { authenticateReportRequest, jsonResponse, proxyReportJsonRequest } from "../_shared";

const DEFAULT_PAGE = 1;
const DEFAULT_LIMIT = 20;

function buildEmptyReportHistoryResponse(request: Request) {
  const url = new URL(request.url);
  const page = Number(url.searchParams.get("page") ?? DEFAULT_PAGE);
  const limit = Number(url.searchParams.get("limit") ?? DEFAULT_LIMIT);
  return {
    data: [],
    page: Number.isFinite(page) && page > 0 ? page : DEFAULT_PAGE,
    limit: Number.isFinite(limit) && limit > 0 ? limit : DEFAULT_LIMIT,
    total: 0,
    has_more: false
  } as const;
}

export async function GET(request: Request) {

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return jsonResponse(JSON.stringify(buildEmptyReportHistoryResponse(request)), 200);
  }

  const url = new URL(request.url);
  const query = url.search ? url.search : "";
  const response = await proxyReportJsonRequest(auth, {
    method: "GET",
    path: `/api/v1/reports${query}`,
    requestId
  });
  if (response.status === 401 || response.status === 403) {
    return jsonResponse(JSON.stringify(buildEmptyReportHistoryResponse(request)), 200);
  }
  return response;
}
