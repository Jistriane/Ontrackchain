import { authenticateReportRequest, proxyReportJsonRequest } from "../_shared";

export async function POST(request: Request) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  return proxyReportJsonRequest(auth, {
    method: "POST",
    path: "/api/v1/reports/ros-coaf",
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
}
