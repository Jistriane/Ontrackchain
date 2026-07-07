import { authenticateReportRequest, proxyReportJsonRequest } from "../../../_shared";

export async function POST(request: Request, context: { params: Promise<{ rosId: string }> }) {
  const { rosId } = await context.params;
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  return proxyReportJsonRequest(auth, {
    method: "POST",
    path: `/api/v1/reports/ros-coaf/${encodeURIComponent(rosId)}/submitted`,
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
}
