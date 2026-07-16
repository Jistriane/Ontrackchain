import { isFrontendStandaloneShowcaseMode } from "../../../../../lib/auth-runtime";
import { getStandaloneShowcaseRosCoafDetail } from "../../../../../lib/standalone-showcase";
import { authenticateReportRequest, jsonResponse, proxyReportJsonRequest } from "../../_shared";

export async function GET(request: Request, context: { params: Promise<{ rosId: string }> }) {
  if (isFrontendStandaloneShowcaseMode()) {
    const { rosId } = await context.params;
    const detail = getStandaloneShowcaseRosCoafDetail(rosId);
    if (!detail) {
      return jsonResponse(JSON.stringify({ error: "ros_not_found" }), 404);
    }
    return jsonResponse(JSON.stringify(detail), 200);
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const { rosId } = await context.params;
  return proxyReportJsonRequest(auth, {
    method: "GET",
    path: `/api/v1/reports/ros-coaf/${encodeURIComponent(rosId)}`,
    requestId
  });
}
