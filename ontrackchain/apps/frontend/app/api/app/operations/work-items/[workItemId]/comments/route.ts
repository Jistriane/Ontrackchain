import { isFrontendStandaloneShowcaseMode } from "../../../../../../lib/auth-runtime";
import { createStandaloneShowcaseWorkItemComment } from "../../../../../../lib/standalone-showcase";
import type { WorkCommentResponse } from "../../../../../../lib/work-item-timeline";
import { authenticateRequest, proxyOperationsRequest } from "../../../_shared";

export async function POST(request: Request, context: { params: Promise<{ workItemId: string }> }) {
  if (isFrontendStandaloneShowcaseMode()) {
    const { workItemId } = await context.params;
    const payload = (await request.json().catch(() => null)) as Pick<WorkCommentResponse, "comment_type" | "body"> | null;
    if (!payload?.body?.trim()) {
      return new Response(JSON.stringify({ error: "invalid_comment_payload" }), {
        status: 422,
        headers: { "content-type": "application/json" }
      });
    }
    const comment = createStandaloneShowcaseWorkItemComment(workItemId, payload);
    if (!comment) {
      return new Response(JSON.stringify({ error: "work_item_not_found" }), {
        status: 404,
        headers: { "content-type": "application/json" }
      });
    }
    return new Response(JSON.stringify(comment), {
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
    method: "POST",
    path: `/api/v1/operations/work-items/${encodeURIComponent(workItemId)}/comments`,
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
}
