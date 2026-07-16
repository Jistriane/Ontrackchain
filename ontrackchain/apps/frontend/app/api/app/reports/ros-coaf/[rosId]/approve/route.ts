import { isFrontendStandaloneShowcaseMode } from "../../../../../../lib/auth-runtime";
import { approveStandaloneShowcaseRosCoaf } from "../../../../../../lib/standalone-showcase";
import { authenticateReportRequest, jsonResponse, proxyReportJsonRequest } from "../../../_shared";

export async function POST(request: Request, context: { params: Promise<{ rosId: string }> }) {
  const { rosId } = await context.params;
  if (isFrontendStandaloneShowcaseMode()) {
    const body = (await request.json().catch(() => null)) as
      | { approved?: boolean; rejection_reason?: string | null }
      | null;
    if (typeof body?.approved !== "boolean") {
      return jsonResponse(JSON.stringify({ error: "invalid_approval_payload" }), 422);
    }
    const result = approveStandaloneShowcaseRosCoaf(rosId, {
      approved: body.approved,
      rejection_reason: body.rejection_reason
    });
    if (!result) {
      return jsonResponse(JSON.stringify({ error: "ros_not_found" }), 404);
    }
    return jsonResponse(JSON.stringify(result), 200);
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateReportRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  return proxyReportJsonRequest(auth, {
    method: "POST",
    path: `/api/v1/reports/ros-coaf/${encodeURIComponent(rosId)}/approve`,
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
}
