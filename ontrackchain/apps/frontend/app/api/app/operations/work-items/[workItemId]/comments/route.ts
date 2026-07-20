import type { WorkCommentResponse } from "../../../../../../lib/work-item-timeline";
import { authenticateRequest, proxyOperationsRequest } from "../../../_shared";

export async function POST(request: Request, context: { params: Promise<{ workItemId: string }> }) {

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
