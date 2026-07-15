import { isFrontendStandaloneShowcaseMode } from "../../../../lib/auth-runtime";
import { resolveStandaloneShowcaseReport } from "../../../../lib/standalone-showcase";
import { canReadReportDetail } from "../../../../lib/authz";
import { authenticateReportRequest, jsonResponse, proxyReportJsonRequest } from "../_shared";

export async function GET(request: Request, context: { params: Promise<{ reportId: string }> }) {
  if (isFrontendStandaloneShowcaseMode()) {
    const { reportId } = await context.params;
    const report = resolveStandaloneShowcaseReport(reportId);
    if (!report || !report.case_id) {
      return jsonResponse(JSON.stringify({ error: "report_not_found" }), 404);
    }
    return jsonResponse(JSON.stringify(report), 200);
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }
  if (!canReadReportDetail(auth.role)) {
    return jsonResponse(JSON.stringify({ detail: "report_detail_role_required" }), 403);
  }

  const { reportId } = await context.params;
  return proxyReportJsonRequest(auth, {
    method: "GET",
    path: `/api/v1/reports/${encodeURIComponent(reportId)}`,
    requestId
  });
}
