import { authenticateReportRequest, proxyReportBinaryRequest } from "../../../_shared";

export async function GET(request: Request, context: { params: Promise<{ rosId: string }> }) {
  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const { rosId } = await context.params;
  const url = new URL(request.url);
  const limit = url.searchParams.get("limit");
  const query = new URLSearchParams();
  if (limit) {
    query.set("limit", limit);
  }

  const suffix = query.toString();
  return proxyReportBinaryRequest(auth, {
    method: "GET",
    path: `/api/v1/reports/ros-coaf/${encodeURIComponent(rosId)}/regulatory-dossier${suffix ? `?${suffix}` : ""}`,
    requestId
  });
}
