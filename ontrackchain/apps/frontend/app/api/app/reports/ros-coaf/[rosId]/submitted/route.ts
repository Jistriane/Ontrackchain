import { isFrontendStandaloneShowcaseMode } from "../../../../../../lib/auth-runtime";
import { submitStandaloneShowcaseRosCoaf } from "../../../../../../lib/standalone-showcase";
import { authenticateReportRequest, jsonResponse, proxyReportJsonRequest } from "../../../_shared";

export async function POST(request: Request, context: { params: Promise<{ rosId: string }> }) {
  const { rosId } = await context.params;
  if (isFrontendStandaloneShowcaseMode()) {
    const body = (await request.json().catch(() => null)) as
      | { coaf_protocol_number?: string | null; coaf_receipt_hash?: string | null }
      | null;
    if (!body?.coaf_protocol_number?.trim()) {
      return jsonResponse(JSON.stringify({ error: "missing_coaf_protocol_number" }), 422);
    }
    const result = submitStandaloneShowcaseRosCoaf(rosId, {
      coaf_protocol_number: body.coaf_protocol_number,
      coaf_receipt_hash: body.coaf_receipt_hash
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
    path: `/api/v1/reports/ros-coaf/${encodeURIComponent(rosId)}/submitted`,
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
}
