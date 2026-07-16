import { isFrontendStandaloneShowcaseMode } from "../../../../../lib/auth-runtime";
import { resolveStandaloneShowcaseRosRef } from "../../../../../lib/standalone-showcase";
import { authenticateReportRequest, jsonResponse, proxyReportJsonRequest } from "../../_shared";

export async function GET(request: Request, context: { params: Promise<{ reportId: string }> }) {
  if (isFrontendStandaloneShowcaseMode()) {
    const { reportId } = await context.params;
    return jsonResponse(JSON.stringify(resolveStandaloneShowcaseRosRef(reportId)), 200);
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return jsonResponse("null", 200);
  }

  const { reportId } = await context.params;
  const response = await proxyReportJsonRequest(auth, {
    method: "GET",
    path: `/api/v1/reports/${encodeURIComponent(reportId)}/ros-coaf-ref`,
    requestId
  });
  if (response.status === 401 || response.status === 403) {
    return jsonResponse("null", 200);
  }
  return response;
}
