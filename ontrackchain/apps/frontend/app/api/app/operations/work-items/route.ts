import {
  isFrontendStandaloneShowcaseMode,
} from "../../../../lib/auth-runtime";
import {
  listStandaloneShowcaseWorkItems,
  upsertStandaloneShowcaseWorkItem
} from "../../../../lib/standalone-showcase";
import type { CreateWorkItemRequest, ReportWorkItemMetadata } from "../../../../lib/work-items";
import { authenticateRequest, proxyOperationsRequest } from "../_shared";

const EMPTY_WORK_ITEMS = {
  data: [],
  page: 1,
  limit: 100,
  total: 0,
  has_more: false
} as const;

export async function GET(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const url = new URL(request.url);
    return new Response(
      JSON.stringify(
        listStandaloneShowcaseWorkItems({
          module: url.searchParams.get("module"),
          resourceType: url.searchParams.get("resource_type"),
          reportExternalId: url.searchParams.get("report_external_id"),
          limit: Number(url.searchParams.get("limit") ?? 100)
        })
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
    return new Response(JSON.stringify(EMPTY_WORK_ITEMS), {
      status: 200,
      headers: { "content-type": "application/json" }
    });
  }

  const url = new URL(request.url);
  const query = url.search ? url.search : "";
  return proxyOperationsRequest(auth, {
    method: "GET",
    path: `/api/v1/operations/work-items${query}`,
    requestId
  });
}

export async function POST(request: Request) {
  if (isFrontendStandaloneShowcaseMode()) {
    const payload = (await request.json().catch(() => null)) as CreateWorkItemRequest<ReportWorkItemMetadata> | null;
    if (!payload?.resource_id || payload?.resource_type !== "formal_report_case" || payload?.module !== "reports") {
      return new Response(JSON.stringify({ error: "invalid_work_item_payload" }), {
        status: 422,
        headers: { "content-type": "application/json" }
      });
    }
    return new Response(
      JSON.stringify(
        upsertStandaloneShowcaseWorkItem({
          ...payload,
          module: "reports",
          resource_type: "formal_report_case"
        })
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

  return proxyOperationsRequest(auth, {
    method: "POST",
    path: "/api/v1/operations/work-items",
    requestId,
    body: await request.text(),
    contentType: "application/json"
  });
}
