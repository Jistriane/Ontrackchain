import { isFrontendStandaloneShowcaseMode } from "../../../../../lib/auth-runtime";
import { getStandaloneShowcaseWorkItem, upsertStandaloneShowcaseWorkItem } from "../../../../../lib/standalone-showcase";
import type { PatchWorkItemRequest, ReportWorkItemMetadata } from "../../../../../lib/work-items";
import { authenticateRequest, proxyOperationsRequest } from "../../_shared";

export async function PATCH(request: Request, context: { params: Promise<{ workItemId: string }> }) {
  if (isFrontendStandaloneShowcaseMode()) {
    const { workItemId } = await context.params;
    const existing = getStandaloneShowcaseWorkItem(workItemId);
    if (!existing) {
      return new Response(JSON.stringify({ error: "work_item_not_found" }), {
        status: 404,
        headers: { "content-type": "application/json" }
      });
    }
    const payload = (await request.json().catch(() => null)) as PatchWorkItemRequest<ReportWorkItemMetadata> | null;
    if (!payload) {
      return new Response(JSON.stringify({ error: "invalid_work_item_payload" }), {
        status: 422,
        headers: { "content-type": "application/json" }
      });
    }
    return new Response(
      JSON.stringify(
        upsertStandaloneShowcaseWorkItem(
          {
            ...existing,
            ...payload,
            resource_id: existing.resource_id,
            case_id: existing.case_id,
            report_external_id: existing.report_external_id,
            module: "reports",
            resource_type: "formal_report_case"
          },
          workItemId
        )
      ),
      {
        status: 200,
        headers: { "content-type": "application/json" }
      }
    );
  }

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
