import { isFrontendStandaloneShowcaseMode } from "../../../../../../lib/auth-runtime";
import { getStandaloneShowcaseWorkItemTimeline } from "../../../../../../lib/standalone-showcase";
import { authenticateRequest, proxyOperationsRequest } from "../../../_shared";

export async function GET(request: Request, context: { params: Promise<{ workItemId: string }> }) {
  if (isFrontendStandaloneShowcaseMode()) {
    const { workItemId } = await context.params;
    const timeline = getStandaloneShowcaseWorkItemTimeline(workItemId);
    if (!timeline) {
      return new Response(JSON.stringify({ error: "work_item_not_found" }), {
        status: 404,
        headers: { "content-type": "application/json" }
      });
    }
    return new Response(JSON.stringify(timeline), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const { workItemId } = await context.params;
  return proxyOperationsRequest(auth, {
    method: "GET",
    path: `/api/v1/operations/work-items/${encodeURIComponent(workItemId)}/timeline`,
    requestId
  });
}
