import { authenticateReportRequest, proxyReportJsonRequest } from "../_shared";

export async function GET(request: Request, context: { params: Promise<{ reportId: string }> }) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const { reportId } = await context.params;
  return proxyReportJsonRequest(auth, {
    method: "GET",
    path: `/api/v1/reports/${encodeURIComponent(reportId)}`,
    requestId
  });
}
