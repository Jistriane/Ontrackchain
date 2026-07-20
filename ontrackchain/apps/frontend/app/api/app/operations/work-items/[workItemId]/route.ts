import type {
  BlocksWorkItemMetadata,
  CounterpartyWorkItemMetadata,
  EvidenceWorkItemMetadata,
  PatchWorkItemRequest,
  ReportWorkItemMetadata,
  RosCoafWorkItemMetadata,
  SanctionsWorkItemMetadata
} from "../../../../../lib/work-items";
import { authenticateRequest, proxyOperationsRequest } from "../../_shared";

export async function PATCH(request: Request, context: { params: Promise<{ workItemId: string }> }) {

  const requestId = request.headers.get("x-request-id") ?? crypto.randomUUID();
  const auth = await authenticateRequest(requestId);
  if (auth instanceof Response) {
    return auth;
  }

  const { workItemId } = await context.params;
  return proxyOperationsRequest(auth, {
    method: "PATCH",
    path: `/api/v1/operations/work-items/${encodeURIComponent(workItemId)}`,
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
}
