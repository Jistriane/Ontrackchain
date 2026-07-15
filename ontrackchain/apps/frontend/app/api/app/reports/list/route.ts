import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import { STANDALONE_SHOWCASE_REPORT_HISTORY } from "../../../../lib/standalone-showcase";
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
  if (isFrontendStandaloneShowcaseMode()) {
    const url = new URL(request.url);
    const page = Number(url.searchParams.get("page") ?? DEFAULT_PAGE);
    const limit = Number(url.searchParams.get("limit") ?? DEFAULT_LIMIT);
    const reportId = url.searchParams.get("report_id")?.trim().toLowerCase() ?? "";
    const reportType = url.searchParams.get("report_type")?.trim().toLowerCase() ?? "";
    const caseId = url.searchParams.get("case_id")?.trim().toLowerCase() ?? "";
    const filtered = STANDALONE_SHOWCASE_REPORT_HISTORY.filter((item) => {
      if (reportId && !item.report_id.toLowerCase().includes(reportId)) return false;
      if (reportType && item.report_type.toLowerCase() !== reportType) return false;
      if (caseId && item.case_id?.toLowerCase() !== caseId) return false;
      return true;
    });
    return jsonResponse(
      JSON.stringify({
        data: filtered.slice(0, limit),
        page: Number.isFinite(page) && page > 0 ? page : DEFAULT_PAGE,
        limit: Number.isFinite(limit) && limit > 0 ? limit : DEFAULT_LIMIT,
        total: filtered.length,
        has_more: filtered.length > limit
      }),
      200
    );
  }

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
